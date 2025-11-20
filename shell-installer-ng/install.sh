#!/usr/bin/env bash
#
# A simple Quobyte installer script using whiptail menu for dialog-based interaction.
#
# Exit immediately if a command exits with a non-zero status.
# Treat unset variables as an error.
# Exit status of a pipeline is the exit status of the last command that failed.
set -euo pipefail

## -----------------------------------------------------------------------------
## Configuration Variables
## -----------------------------------------------------------------------------
readonly QUOBYTE_REPO_URL="https://packages.quobyte.com/repo/current"
readonly PACKAGE_NAMES_RPM="quobyte-server quobyte-tools java-21-openjdk-headless"
readonly PACKAGE_NAMES_DEB="quobyte-server quobyte-tools default-jre-headless"
readonly INSTALL_LOG="/tmp/quobyte_install_$(date +%F-%T).log"

SSH_USER_INIT="${USER:-$(whoami)}" # Use $USER if set, otherwise fallback to whoami
UNINSTALL="false"
NODES=""
SSH_USER=""
REGISTRY_STRING=""
PUBLIC_IP=""
qns_id="" # Variable to hold the generated QNS ID
qns_secret="" # Variable to hold the generated QNS Secret

# Set Quobyte green background for whiptail
export NEWT_COLORS="root=,green:"
export TERM="ansi" # Ensure whiptail uses the correct terminal type

## -----------------------------------------------------------------------------
## Core Dialog Functions
## -----------------------------------------------------------------------------

# Wrapper for whiptail to swap STDOUT and STDERR for piping.
# Usage: menu --title "Title" --msgbox "Message" 10 80
menu() {
    whiptail "$@" 3>&1 1>&2 2>&3 3>&-
}

check_installer_requirements() {
    local missing_tools=()

    # Check local dependencies
    for tool in whiptail uuidgen curl; do
        if ! command -v "$tool" > /dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -gt 0 ]; then
        echo "failure"
        echo "Missing required local commands: ${missing_tools[*]}" >&2
        return 1
    fi
    echo "success"
}

welcome_dialog() {
    menu --title "Quobyte Installer" \
        --msgbox "Welcome to the Quobyte software installer! This script will guide you through the process of setting up a new Quobyte cluster." 10 80
}

checklist_dialog() {
    menu --title "Quobyte Installer" --yesno "Requirements Checklist:\n\
\n\
* At least 4 Linux machines\n\
* At least two unformatted devices per machine\n\
* Machines can access the internet\n\
* No firewall blocking Quobyte traffic between machines\n\
* Port 8080 open to access Quobyte via web browser\n\
* SSH access (key-based preferred) to all machines\n\
* SSH user must have NOPASSWD sudo access.\n\
* A time sync daemon (chrony or ntpd) active on all machines\n\
* A text file containing all target machines, one per line\n\
\n\
Are you prepared to install Quobyte?" 23 80
}

## -----------------------------------------------------------------------------
## Input Validation and Gathering Functions
## -----------------------------------------------------------------------------

check_user_input() {
    # Used for ssh user names and node names.
    local input="$1"
    if [[ "$input" =~ ^[a-z0-9][-a-z0-9_.]*$ ]]; then
        echo "$input"
    else
        echo "Invalid"
    fi
}

get_ssh_user() {
    local username_accepted="init"
    local ssh_user_raw=""

    while [ "${username_accepted}" = "init" ]; do
        ssh_user_raw=$(menu --title "Quobyte Installer" --inputbox "Please enter the user name to connect via SSH to the target nodes." 10 80 "${SSH_USER_INIT}")
        local exit_status=$?

        if [ $exit_status -ne 0 ]; then
            echo "Installation canceled by user." >&2
            exit 1
        fi

        if [[ $(check_user_input "${ssh_user_raw}") != "Invalid" ]]; then
            username_accepted="accepted"
            echo "${ssh_user_raw}"
        else
            menu --title "Error" --yesno --yes-button "Retry" --no-button "Exit" "${ssh_user_raw} is an invalid user name." 10 80
            if [ $? -ne 0 ]; then
                echo "Installation canceled by user." >&2
                exit 1
            fi
        fi
    done
}

get_nodes() {
    local node_file_path="init"
    local -a nodes_array=()

    while [ "${node_file_path}" = "init" ]; do
        node_file_path=$(menu --title "Quobyte Installer" --inputbox "Please enter the full path to a file containing your install target nodes." 10 80)
        local exit_status=$?

        if [ $exit_status -ne 0 ]; then
            echo "Installation canceled by user." >&2
            exit 1
        fi

        if [ ! -f "$node_file_path" ]; then
            menu --title "Error" --yesno --yes-button "Retry" --no-button "Exit" "The file '$node_file_path' was not found." 10 80
            if [ $? -ne 0 ]; then
                exit 1
            else
                node_file_path="init" # Loop again
            fi
        fi
    done

    # Read nodes from the validated file
    while IFS= read -r line; do
        # Remove leading/trailing whitespace using robust substitution
        local line_trimmed="${line##*( )}"
        line_trimmed="${line_trimmed%%*( )}"

        # Skip comment lines and blank lines
        case "$line_trimmed" in
            \#*) continue ;;
            "") continue ;;
        esac

        if [[ $(check_user_input "$line_trimmed") != "Invalid" ]]; then
            nodes_array+=( "${line_trimmed}" )
        else
            menu --title "Error" --msgbox "Node \"$line_trimmed\" is not allowed as hostname." 10 80
            exit 1
        fi
    done < "$node_file_path"

    if [ ${#nodes_array[@]} -eq 0 ]; then
        menu --title "Error" --msgbox "The node file is empty or only contains invalid entries." 10 80
        exit 1
    fi

    # Display nodes to the user
    local node_list_display=$(printf "%s\n" "${nodes_array[@]}")
    menu --title "Quobyte Installer" --msgbox "Going to install Quobyte on these nodes:\n\n${node_list_display}" 16 80

    echo "Install on these target nodes: ${nodes_array[*]}" >> "$INSTALL_LOG"
    # Output space-separated list of nodes
    echo "${nodes_array[*]}"
}

## -----------------------------------------------------------------------------
## Pre-flight Checks
## -----------------------------------------------------------------------------

check_sudo_nopasswd() {
    local node="$1"
    echo "Checking passwordless sudo access on $node..." >> "$INSTALL_LOG"

    # Try to execute a benign sudo command (-n means no password prompt)
    if ! ssh "${SSH_USER}@${node}" "sudo -n true" > /dev/null 2>&1; then
        menu --title "Error" --msgbox "Error: SSH user ${SSH_USER} on ${node} requires a password for 'sudo'. Please configure NOPASSWD access." 10 80
        echo "Error: Passwordless sudo check failed on ${node}." >> "$INSTALL_LOG"
        return 1
    fi

    echo "Passwordless sudo access verified on $node." >> "$INSTALL_LOG"
    return 0
}

check_connectivity() {
    local node="$1"
    menu --infobox "Checking SSH and repository connectivity on node $node..." 10 80
    echo "Checking connectivity to $node..." >> "$INSTALL_LOG"

    # Check SSH availability
    if ! ssh -o ConnectTimeout=5 "${SSH_USER}@${node}" "exit"; then
        menu --title "Error" --msgbox "Error: SSH connection with user ${SSH_USER} to ${node} failed." 10 80
        echo "Error: SSH connection to ${node} failed." >> "$INSTALL_LOG"
        return 1
    fi

    # Check HTTPS connectivity from the target node
    if ! ssh "${SSH_USER}@${node}" "curl -s -o /dev/null -w '%{http_code}' ${QUOBYTE_REPO_URL}" | grep -q "200"; then
        menu --title "Error" --msgbox "Error: ${node} cannot reach ${QUOBYTE_REPO_URL}" 10 80
        echo "Error: ${node} cannot reach ${QUOBYTE_REPO_URL}" >> "$INSTALL_LOG"
        return 1
    fi

    return 0
}

check_timesync() {
    local node="$1"
    local failed_timesync_check=1
    local daemon

    echo "Checking time sync daemon on $node" >> "$INSTALL_LOG"
    menu --infobox "Checking time sync daemon on $node..." 10 80

    for daemon in ntp ntpd chrony chronyd; do
        if ssh "${SSH_USER}@${node}" "sudo systemctl is-active ${daemon} > /dev/null 2>&1"; then
            failed_timesync_check=0
            break
        fi
    done

    if [ ${failed_timesync_check} -eq 0 ]; then
        echo "Found active time sync daemon on $node" >> "$INSTALL_LOG"
        menu --infobox "Found active time sync daemon on $node..." 10 80
    else
        echo "Did not find active time sync daemon on $node, exit" >> "$INSTALL_LOG"
        menu --msgbox "No active time sync daemon on $node. Please install chrony or ntpd before proceeding." 10 80
        exit 1
    fi
}

check_previous_installation() {
    local node="$1"
    echo "Checking for previous Quobyte data on $node..." >> "$INSTALL_LOG"

    # Check for the existence of the device setup file, which indicates installed Quobyte data.
    # Returns 1 if found (true), 0 if not found (false).
    # What we want is absence of that file.
    if ssh "${SSH_USER}@${node}" "sudo test -f /var/lib/quobyte/devices/*/QUOBYTE_DEV_SETUP"; then
        return 1
    else
        return 0
    fi
}

check_distrosupport() {
    local node="$1"
    echo "Checking Linux distribution support on $node" >> "$INSTALL_LOG"
    local distro
    # Use 'source' to safely load /etc/os-release and access $ID
    distro=$(ssh "${SSH_USER}@${node}" 'source /etc/os-release && echo "$ID"')

    case "$distro" in
        rocky|almalinux|centos|ubuntu|debian|opensuse-leap|sles)
            echo "Found supported distribution $distro on $node, proceeding" >> "$INSTALL_LOG"
            ;;
        *)
            echo "Unsupported Linux distribution: $distro on node $node" >> "$INSTALL_LOG"
            menu --title "Error" --msgbox "Unsupported Linux distribution: $distro on node $node." 10 80
            exit 1
            ;;
    esac
}

get_distro_info() {
    local node="$1"
    local distro=""
    local version=""
    local version_codename=""
    local major_version=""
    local package_manager=""

    # Get OS details in one SSH call
    local os_info
    os_info=$(ssh "${SSH_USER}@${node}" 'source /etc/os-release 2>/dev/null; echo "$ID:$VERSION_ID:$VERSION_CODENAME"')

    IFS=':' read -r distro version version_codename <<< "$os_info"

    # Extract major version
    major_version=$(echo "${version}" | cut -d'.' -f1)

    case "$distro" in
        rocky|almalinux|centos)
            package_manager="dnf"
            ;;
        ubuntu|debian)
            package_manager="apt"
            ;;
        opensuse-leap|sles)
            package_manager="zypper"
            ;;
        *)
            echo "Unsupported Linux distribution $distro." >&2
            exit 1
            ;;
    esac

    # Return colon-separated string
    echo "$distro:$version:$major_version:$package_manager:$version_codename"
}

## -----------------------------------------------------------------------------
## Installation Steps
## -----------------------------------------------------------------------------

install_repo() {
    local node="$1"
    local distro_info="$2"
    IFS=':' read -r distro version major_version package_manager version_codename <<< "$distro_info"

    local quobyte_distro_alias=""
    local repo_url=""
    local failed_repo=0

    # Determine Quobyte distribution alias
    case "$distro" in
        rocky|almalinux) quobyte_distro_alias="RockyLinux" ;;
        centos) quobyte_distro_alias="CentOS" ;;
        ubuntu|debian) quobyte_distro_alias="" ;;
        opensuse-leap|sles) quobyte_distro_alias="SLE" ;;
        *) echo "Unsupported distribution logic in install_repo." >&2; exit 1 ;;
    esac

    echo "Adding Quobyte repository on $node ($distro $version)..." >> "$INSTALL_LOG"

    case "$distro" in
        rocky|almalinux|centos)
            repo_url="${QUOBYTE_REPO_URL}/rpm/${quobyte_distro_alias}_${major_version}/"
            ssh "${SSH_USER}@${node}" "sudo ${package_manager} config-manager --add-repo ${repo_url}quobyte.repo" >> "$INSTALL_LOG" 2>&1 || failed_repo=1
            ;;
        opensuse-leap|sles)
            repo_url="${QUOBYTE_REPO_URL}/rpm/${quobyte_distro_alias}_${major_version}/"
            ssh "${SSH_USER}@${node}" "sudo ${package_manager} addrepo ${repo_url} quobyte" >> "$INSTALL_LOG" 2>&1 || failed_repo=1
            ;;
        ubuntu|debian)
            repo_url="${QUOBYTE_REPO_URL}/apt"
            ssh "${SSH_USER}@${node}" "sudo sh -c 'curl -s ${repo_url}/pubkey.gpg | gpg --dearmor > /etc/apt/trusted.gpg.d/quobyte.gpg'" >> "$INSTALL_LOG" 2>&1 || failed_repo=1
            ssh "${SSH_USER}@${node}" "sudo sh -c 'echo \"deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/quobyte.gpg] ${repo_url} ${version_codename} main\" > /etc/apt/sources.list.d/quobyte.list' && sudo apt-get update" >> "$INSTALL_LOG" 2>&1 || failed_repo=1
            ;;
        *)
            echo "Unsupported distribution logic in install_repo (post-alias)." >&2
            exit 1
            ;;
    esac

    if [ ${failed_repo} -ne 0 ]; then
        echo "Failed to install repository on $node." >&2
        return 1
    fi

    echo "Repository installed successfully on $node." >> "$INSTALL_LOG"
}

install_packages() {
    local node="$1"
    local package_manager="$2"
    local failed_packages=0

    echo "Installing packages on $node using package manager ${package_manager}..." >> "$INSTALL_LOG"

    if [ "$package_manager" = "dnf" ] || [ "$package_manager" = "yum" ] ; then
        ssh "${SSH_USER}@${node}" "sudo ${package_manager} install -y ${PACKAGE_NAMES_RPM}" >> "$INSTALL_LOG" 2>&1 || failed_packages=1
    elif [ "$package_manager" = "zypper" ]; then
        ssh "${SSH_USER}@${node}" "sudo ${package_manager} --gpg-auto-import-keys --non-interactive install ${PACKAGE_NAMES_RPM}" >> "$INSTALL_LOG" 2>&1 || failed_packages=1
    elif [ "$package_manager" = "apt" ]; then
        ssh "${SSH_USER}@${node}" "sudo DEBIAN_FRONTEND=noninteractive ${package_manager} -o Apt::Cmd::Disable-Script-Warning=true install -y ${PACKAGE_NAMES_DEB}" >> "$INSTALL_LOG" 2>&1 || failed_packages=1
    else
        echo "Unknown package manager ${package_manager}." >&2
        exit 1
    fi

    if [ ${failed_packages} -ne 0 ]; then
        echo "Failed to install packages on $node." >&2
        echo "Installation was not successful." >&2
        exit 1
    fi

    echo "Packages installed successfully on $node." >> "$INSTALL_LOG"
    return 0
}

setup_qns() {
    # Generate UUIDs for QNS ID and Secret
    local qns_id_raw=$(uuidgen | tr -d '-')
    local qns_secret_raw=$(uuidgen | tr -d '-')

    # Quobyte uses 12 char ID and 24 char secret
    # Assign to global variables for use in bootstrap_quobyte
    qns_id="${qns_id_raw:0:12}"
    qns_secret="${qns_secret_raw:0:24}"

    REGISTRY_STRING="registry = ${qns_id}.myquobyte.net"
    menu --title "Info" --infobox "A new cluster record has been created:\n\n${REGISTRY_STRING}" 10 80
}

find_public_ip() {
    local node="$1"
    local public_ip

    # Use a common service to get external IP
    public_ip=$(ssh "${SSH_USER}@${node}" "curl -s ifconfig.me")

    if [ -z "$public_ip" ]; then
        echo "Could not find public IP for $node." >&2
        return 1
    fi

    echo "$public_ip"
}

bootstrap_quobyte() {
    local node="$1"
    echo "Bootstrapping Quobyte cluster on $node..." >> "$INSTALL_LOG"
    echo "QNS ID: ${qns_id}" >> "$INSTALL_LOG"
    echo "QNS Secret: ${qns_secret}" >> "$INSTALL_LOG"
    echo "Registry endpoint: ${REGISTRY_STRING}" >> "$INSTALL_LOG"

    # 1. Setup registry data directory and bootstrap
    ssh "${SSH_USER}@${node}" "sudo mkdir -p /var/lib/quobyte/devices/registry-data"
    ssh "${SSH_USER}@${node}" "sudo /usr/bin/qbootstrap -y -d /var/lib/quobyte/devices/registry-data" >> "$INSTALL_LOG" 2>&1

    # 2. Set ownership
    ssh "${SSH_USER}@${node}" "sudo chown -R quobyte:quobyte /var/lib/quobyte"

    # 3. Configure host.cfg and registry.cfg
    ssh "${SSH_USER}@${node}" "sudo sed -i 's/^registry.*/${REGISTRY_STRING}/g' /etc/quobyte/host.cfg"
    ssh "${SSH_USER}@${node}" "sudo grep 'qns.id' /etc/quobyte/registry.cfg || echo 'qns.id = ${qns_id}' | sudo tee -a /etc/quobyte/registry.cfg"
    ssh "${SSH_USER}@${node}" "sudo grep 'qns.secret' /etc/quobyte/registry.cfg || echo 'qns.secret = ${qns_secret}' | sudo tee -a /etc/quobyte/registry.cfg"

    # 4. Enable and restart services
    local services=(quobyte-registry quobyte-api quobyte-webconsole quobyte-data quobyte-metadata)
    for service in "${services[@]}"; do
        ssh "${SSH_USER}@${node}" "sudo systemctl enable --quiet ${service}" >> "$INSTALL_LOG"
        ssh "${SSH_USER}@${node}" "sudo systemctl restart ${service}" >> "$INSTALL_LOG"
    done
}

join_quobyte() {
    local node="$1"
    echo "Joining $node to the bootstrapped cluster..." >> "$INSTALL_LOG"

    # 1. Create registry device (for joining nodes)
    ssh "${SSH_USER}@${node}" "sudo mkdir -p /var/lib/quobyte/devices/registry-data"
    ssh "${SSH_USER}@${node}" "sudo /usr/bin/qmkdev -t REGISTRY -d /var/lib/quobyte/devices/registry-data" >> "$INSTALL_LOG" 2>&1

    # 2. Set ownership
    ssh "${SSH_USER}@${node}" "sudo chown -R quobyte:quobyte /var/lib/quobyte"

    # 3. Configure host.cfg
    ssh "${SSH_USER}@${node}" "sudo sed -i 's/^registry.*/${REGISTRY_STRING}/g' /etc/quobyte/host.cfg"

    # 4. Enable and restart services
    local services=(quobyte-registry quobyte-api quobyte-webconsole quobyte-data quobyte-metadata)
    for service in "${services[@]}"; do
        ssh "${SSH_USER}@${node}" "sudo systemctl enable --quiet ${service}" >> "$INSTALL_LOG"
        ssh "${SSH_USER}@${node}" "sudo systemctl restart ${service}" >> "$INSTALL_LOG"
    done
}

## -----------------------------------------------------------------------------
## Uninstallation Steps
## -----------------------------------------------------------------------------

remove_packages() {
    local node="$1"
    local package_manager="$2"

    echo "Stopping Quobyte services on $node..." >> "$INSTALL_LOG"
    local services=(quobyte-data quobyte-metadata quobyte-api quobyte-registry quobyte-webconsole)
    for service in "${services[@]}"; do
        ssh "${SSH_USER}@${node}" "sudo systemctl stop ${service}" 2>/dev/null || true # Ignore errors if services are not running
    done

    echo "Removing packages on $node using package manager ${package_manager}..." >> "$INSTALL_LOG"

    local exit_code=0
    if [ "$package_manager" = "dnf" ] || [ "$package_manager" = "yum" ]; then
        ssh "${SSH_USER}@${node}" "sudo ${package_manager} remove -y ${PACKAGE_NAMES_RPM}" >> "$INSTALL_LOG" 2>&1 || exit_code=$?
    elif [ "$package_manager" = "zypper" ]; then
        ssh "${SSH_USER}@${node}" "sudo ${package_manager} remove -y ${PACKAGE_NAMES_RPM}" >> "$INSTALL_LOG" 2>&1 || exit_code=$?
        ssh "${SSH_USER}@${node}" "sudo ${package_manager} removerepo quobyte" >> "$INSTALL_LOG" 2>&1
    elif [ "$package_manager" = "apt" ]; then
        ssh "${SSH_USER}@${node}" "sudo ${package_manager} purge -y ${PACKAGE_NAMES_DEB}" >> "$INSTALL_LOG" 2>&1 || exit_code=$?
        ssh "${SSH_USER}@${node}" "sudo rm -f /etc/apt/sources.list.d/quobyte.list" >> "$INSTALL_LOG" 2>&1
        ssh "${SSH_USER}@${node}" "sudo rm -f /etc/apt/trusted.gpg.d/quobyte.gpg" >> "$INSTALL_LOG" 2>&1
    else
        echo "Unknown package manager ${package_manager}." >&2
        return 1
    fi

    if [ $exit_code -ne 0 ]; then
        echo "Warning: Failed to remove some packages on $node. Continuing with state removal." >> "$INSTALL_LOG"
    fi

    echo "Packages removal attempt completed on $node." >> "$INSTALL_LOG"
    return 0
}

remove_state() {
    local node="$1"

    echo "Removing Quobyte data and configuration state on $node..." >> "$INSTALL_LOG"

    # 1. Unmount and wipe devices (assuming Quobyte labels them)
    local devices
    # Note: Using sed instead of awk/grep here for a potentially more robust one-liner on the remote host
    devices=$(ssh "${SSH_USER}@${node}" "lsblk -o NAME,LABEL | grep 'quobyte-dev' | sed 's/ .*//g'")

    for device in ${devices}; do
        echo "Unmounting /dev/${device}..." >> "$INSTALL_LOG"
        ssh "${SSH_USER}@${node}" "sudo umount /dev/${device}" 2>/dev/null || true
        echo "Wiping /dev/${device}..." >> "$INSTALL_LOG"
        ssh "${SSH_USER}@${node}" "sudo wipefs -a /dev/${device}" 2>/dev/null || true
    done

    # 2. Remove configuration and data directories
    echo "Removing /var/lib/quobyte and /etc/quobyte..." >> "$INSTALL_LOG"
    ssh "${SSH_USER}@${node}" "sudo rm -rf /var/lib/quobyte"
    ssh "${SSH_USER}@${node}" "sudo rm -rf /etc/quobyte"

    echo "State removed from $node." >> "$INSTALL_LOG"
}

## -----------------------------------------------------------------------------
## Utility & Usage
## -----------------------------------------------------------------------------

usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h             Show this help message and exit."
    echo "  -u             Uninstall. Erases any data and deletes your Quobyte cluster"
    exit 0
}

## -----------------------------------------------------------------------------
## Main Script Execution
## -----------------------------------------------------------------------------

# Parse arguments
while getopts ":hu" opt; do
    case "${opt}" in
        h)
            usage
            ;;
        u)
            UNINSTALL="true"
            ;;
        \?)
            echo "Error: Invalid option: -${OPTARG}" >&2
            usage
            ;;
    esac
done
shift $((OPTIND - 1)) # Consume processed arguments

# 1. Welcome and dependency check
local_req_status=$(check_installer_requirements)
if [[ ! "$local_req_status" == "success" ]]; then
    # Error message is already echoed by check_installer_requirements
    exit 1
else
    welcome_dialog
fi

# 2. Checklist and initial input
checklist_dialog || exit 1
NODES=$(get_nodes)
SSH_USER=$(get_ssh_user)

# Convert space-separated string of nodes into an array
IFS=' ' read -r -a nodes_array <<< "$NODES"

# --- UNINSTALL PATH ---
if [ "$UNINSTALL" = "true" ]; then
    menu --title "Warning" --yesno --yes-button "Continue" --no-button "Cancel" "You are about to UNINSTALL Quobyte. This process will STOP all services, DELETE all Quobyte software packages, and ERASE ALL Quobyte data and configuration state. Are you sure you want to proceed?" 15 80 || exit 1

    for node in "${nodes_array[@]}"; do
        distro_info=$(get_distro_info "$node")
        package_manager=$(echo "$distro_info" | cut -d':' -f4)
        remove_packages "$node" "$package_manager"
        remove_state "$node"
    done
    menu --title "Uninstallation Complete" --msgbox "Quobyte uninstallation is complete. Packages and state have been removed from the target nodes." 10 80
    exit 0
fi
# ----------------------

# --- INSTALL PATH ---

# 3. Pre-installation checks on all nodes
for node in "${nodes_array[@]}"; do
    if ! check_connectivity "$node"; then
        echo "Could not connect to node $node, exit installation" >&2
        exit 1
    fi
    if ! check_sudo_nopasswd "$node"; then
        echo "Passwordless sudo is required on node $node, exit installation" >&2
        exit 1
    fi
    # check_timesync includes an exit on failure, so no explicit check here.
    check_timesync "$node"
    # check_distrosupport includes an exit on failure, so no explicit check here.
    check_distrosupport "$node"
done

# 4. Process each node (Install and Bootstrap/Join)
first_node_flag=true

for node in "${nodes_array[@]}"; do
    echo "Processing node: $node" >> "$INSTALL_LOG"

    # Get distro info once
    distro_info=$(get_distro_info "$node")
    package_manager=$(echo "$distro_info" | cut -d':' -f4)

    # 4a. Install software sources list
    install_repo "$node" "$distro_info"

    # 4b. Install packages
    install_packages "$node" "$package_manager"

    # 4c. Quobyte bootstrap and cluster join
    if "$first_node_flag"; then
        if check_previous_installation "$node"; then
            menu --title "Error" --msgbox "Error: Previous Quobyte data detected on ${node}. Please run the uninstallation path (-u) first or remove data manually." 10 80
            exit 1
        fi

        setup_qns # Creates $qns_id, $qns_secret, and $REGISTRY_STRING
        bootstrap_quobyte "$node"

        # Find public IP for final access message
        PUBLIC_IP=$(find_public_ip "$node" || true) # Use || true to prevent immediate script exit on finding no IP

        if [ -n "$PUBLIC_IP" ]; then
            first_node_flag=false
        else
            echo "Could not get public IP for the first node. Cannot continue." >&2
            exit 1
        fi
    else
        join_quobyte "$node"
    fi
done

# 5. Final welcome message
if [ -n "$PUBLIC_IP" ]; then
    menu --title "Installation Complete" --msgbox "Congratulations! The Quobyte cluster has been installed. Please open your web browser and navigate to:\n\nhttp://${PUBLIC_IP}:8080\n\nto complete the setup." 15 70
else
    menu --title "Installation Failed" --msgbox "The installation completed, but the public IP could not be determined. Please check the logs in ${INSTALL_LOG} for errors." 15 70
fi

