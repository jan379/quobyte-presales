#!/usr/bin/env bash

# A simple Quobyte installer script using whiptail for dialog-based interaction.


# --- Configuration Variables ---
QUOBYTE_REPO_URL="https://packages.quobyte.com/repo/current"
PACKAGE_NAMES_RPM="quobyte-server quobyte-tools java-21-openjdk-headless"
PACKAGE_NAMES_DEB="quobyte-server quobyte-tools default-jre-headless"
SSH_USER="unset-user"
TERM="ansi"
INSTALL_LOG="/tmp/quobyte_install_$(date +%F-%T).log"
# Set Quobyte green background
export NEWT_COLORS="root=,green:"
# For passwordless SSH, you'd use a key. For a password, you might use 'sshpass' or similar.
# This script assumes SSH keys are in place for security.

# --- Function Definitions ---

welcome_dialog() {
    whiptail --title "Quobyte Installer" --msgbox "Welcome to the Quobyte software installer! This script will guide you through the process of setting up a new Quobyte cluster." 10 60
}

checklist_dialog() {
    whiptail --title "Quobyte Installer" --yesno "Requirements Checklist:\n\
            \n\
            * At least 4 Linux machines\n\
            * At least two unformatted devices\n\
	      per machine\n\
            * Machines can access the internet\n\
            * No firewall blocking Quobyte traffic\n\
	      between machines\n\
            * Port 8080 open to access Quobyte via\n\
	      web browser\n\
            * SSH access to all machines\n\
	    * A time sync daemon (chrony or ntpd)\n\
	      active on all machines\n\
	    * A text file containing all machines\n\
	      one per line\n\
            \n\
	    Are you prepared to install Quobyte?\n\
            " 23 60
}


get_ssh_user() {
    SSH_USER=$(whiptail --title "Quobyte Installer" --inputbox "Please enter the user name to connect via SSH to the target nodes." 10 60 3>&1 1>&2 2>&3)
    echo "${SSH_USER}"
}

get_node_file() {
    NODE_FILE=$(whiptail --title "Quobyte Installer" --inputbox "Please enter the full path to the file containing your install target nodes." 10 60 3>&1 1>&2 2>&3)
    
    if [ $? -ne 0 ]; then
        echo "Installation canceled by user."
        exit 1
    fi
    
    if [ ! -f "$NODE_FILE" ]; then
        whiptail --title "Error" --msgbox "The file '$NODE_FILE' was not found." 10 60
        exit 1
    fi
    echo "$NODE_FILE"
}

check_connectivity() {
    local node=$1
    echo "Checking connectivity to $node..."
    # Check SSH availability
    if ! ssh "$SSH_USER@$node" exit; then
        echo "Error: SSH connection to $node failed."
        return 1 
    fi

    # Check HTTPS connectivity from the target node
    if ! ssh "$SSH_USER@$node" "curl -s -o /dev/null -w '%{http_code}' $QUOBYTE_REPO_URL" | grep -q "200"; then
        echo "Error: Target $node cannot reach $QUOBYTE_REPO_URL"
        return 1
    fi
    return 0
}

check_timesync(){
    local node=$1
    echo "Checking time sync daemon "
    for daemon in ntp ntpd chrony chronyd; do
        ssh $SSH_USER@$node "sudo systemctl is-active $daemon > /dev/null" && echo "Found active time sync daemon $daemon".
    done
}

check_distrosupport(){
    local node=$1
    echo "Checking Linux distribution support "
    local distro=$(ssh "$SSH_USER@$node" 'source /etc/os-release && echo "$ID"')
    case "$distro" in
        rocky|almalinux|centos|ubuntu|debian|opensuse-leap)
            echo "Found distribution $distro on $node, proceeding"
            ;;
        *)
            echo "Unsupported Linux distribution: $distro on node $node"
            exit 1
            ;;
    esac
}

get_distro_info() {
    local node=$1
    local distro=$(ssh "$SSH_USER@$node" 'source /etc/os-release && echo "$ID"')
    local version=$(ssh "$SSH_USER@$node" 'source /etc/os-release && echo "$VERSION_ID"')
    local version_codename=$(ssh "$SSH_USER@$node" 'source /etc/os-release && echo "$VERSION_CODENAME"')
    local major_version=$(echo ${version} | awk -F\. '{print $1'})
    case "$distro" in
        rocky|almalinux|centos)
	   package_manager="dnf"
	   ;;
        ubuntu|debian)
	   package_manager="apt"
	   ;;
        opensuse-leap)
	   package_manager="zypper"
	   ;;
        *)
	   echo "Unsupported Linux distribution $distro."
           exit 1
	   ;;
    esac
    echo "$distro:$version:$major_version:$package_manager:$version_codename"
}

install_repo() {
    local node=$1
    local distro_info=$2
    local distro=$(echo "$distro_info" | cut -d':' -f1)
    local version=$(echo "$distro_info" | cut -d':' -f2)
    local major_version=$(echo "$distro_info" | cut -d':' -f3)
    local package_manager=$(echo "$distro_info" | cut -d':' -f4)
    local version_codename=$(echo "$distro_info" | cut -d':' -f5)
    case "$distro" in
        rocky|almalinux)
            local quobyte_distro_alias="RockyLinux"
            ;;
        centos)
	    local quobyte_distro_alias="CentOS"
            ;;
        ubuntu|debian)
            local quobyte_distro_alias="unset"
            ;;
        opensuse-leap)
            local quobyte_distro_alias="SLE"
	    ;;
        *)
            echo "Unsupported Linux distribution: $distro"
            exit 1
            ;;
    esac

    echo "Adding Quobyte repository on $node ($distro $version)..."
    
    REPO_URL=""
    failed_repo=0
    case "$distro" in
        rocky|almalinux|centos)
            REPO_URL="${QUOBYTE_REPO_URL}/rpm/${quobyte_distro_alias}_${major_version}/"
            ssh "$SSH_USER@$node" "sudo ${package_manager} config-manager --add-repo ${REPO_URL}quobyte.repo" >> $INSTALL_LOG || failed_repo=1
            ;;
        opensuse-leap)
            REPO_URL="${QUOBYTE_REPO_URL}/rpm/${quobyte_distro_alias}_${major_version}/"
            ssh "$SSH_USER@$node" "sudo ${package_manager} addrepo --gpg-auto-import-keys ${REPO_URL} quobyte" >> $INSTALL_LOG || failed_repo=1
            ;;
        ubuntu|debian)
            REPO_URL="${QUOBYTE_REPO_URL}/apt"
            ssh "$SSH_USER@$node" "sudo sh -c 'curl -s ${REPO_URL}/pubkey.gpg | gpg --dearmor > /etc/apt/trusted.gpg.d/quobyte.gpg'" >> $INSTALL_LOG || failed_repo=1
            ssh "$SSH_USER@$node" "sudo sh -c 'echo \"deb [arch=amd64 signed-by=/etc/apt/trusted.gpg.d/quobyte.gpg] ${REPO_URL} ${version_codename} main\" > /etc/apt/sources.list.d/quobyte.list' && sudo apt-get update" >> $INSTALL_LOG || failed_repo=1
            ;;
        *)
            echo "Unsupported Linux distribution: $distro"
            exit 1
            ;;
    esac
    
    if [ ${failed_repo} -ne 0 ]; then
        echo "Failed to install repository on $node."
        return 1
    fi

    echo "Repository installed successfully."
    echo "$PACKAGE_MANAGER"
}

install_packages() {
    local node=$1
    local package_manager=$2
    local failed_packages=0

    echo "Installing packages on $node using package manager ${package_manager}..."
    
    if [ "$package_manager" == "dnf" ] || [ "$package_manager" == "yum" ] || [ "$package_manager" == "zypper" ]; then
        ssh "$SSH_USER@$node" "sudo $package_manager install -y $PACKAGE_NAMES_RPM" >> $INSTALL_LOG || failed_packages=1
    elif [ "$package_manager" == "apt" ]; then
        ssh "$SSH_USER@$node" "sudo DEBIAN_FRONTEND=noninteractive $package_manager -o Apt::Cmd::Disable-Script-Warning=true install -y $PACKAGE_NAMES_DEB" 2>&1 >> $INSTALL_LOG || failed_packages=1
    else
        echo "Unknown package manager ${package_manager}."
        exit 1
    fi
    
    if [ ${failed_packages} -ne 0 ]; then
        echo "Failed to install packages on $node."
        echo "Installation was not successful."
        exit 1
    fi

    echo "Packages installed successfully."
    return 0
}

remove_packages() {
    local node=$1
    local package_manager=$2

    echo "Removing packages on $node using package manager ${package_manager}..."
    ssh "$SSH_USER@$node" "sudo systemctl stop quobyte-data" 
    ssh "$SSH_USER@$node" "sudo systemctl stop quobyte-metadata" 
    ssh "$SSH_USER@$node" "sudo systemctl stop quobyte-api" 
    ssh "$SSH_USER@$node" "sudo systemctl stop quobyte-registry" 
    ssh "$SSH_USER@$node" "sudo systemctl stop quobyte-webconsole" 
        
    if [ "$package_manager" == "dnf" ] || [ "$package_manager" == "yum" ]; then
        ssh "$SSH_USER@$node" "sudo $package_manager remove -y $PACKAGE_NAMES_RPM" 
    elif [ "$package_manager" == "zypper" ]; then
        ssh "$SSH_USER@$node" "sudo $package_manager remove -y $PACKAGE_NAMES_RPM" 
        ssh "$SSH_USER@$node" "sudo $package_manager removerepo quobyte" 
    elif [ "$package_manager" == "apt" ]; then
        ssh "$SSH_USER@$node" "sudo $package_manager purge -y $PACKAGE_NAMES_DEB" 
        ssh "$SSH_USER@$node" "sudo rm /etc/apt/sources.list.d/quobyte.list" 
        ssh "$SSH_USER@$node" "sudo rm /etc/apt/trusted.gpg.d/quobyte.gpg" 
    else
        echo "Unknown package manager ${package_manager}."
        return 1
    fi
    
    if [ $? -ne 0 ]; then
        echo "Failed to remove packages on $node."
        return 1
    fi

    echo "Packages removed successfully."
    return 0
}

remove_state() {
    local node=$1
    local devices=$(ssh $SSH_USER@$node "lsblk -o name,label | grep quobyte-dev | sed s/\ .*//g")
    for device in $devices; do 
  	ssh $SSH_USER@$node "sudo umount /dev/$device"
    done
    for device in $devices; do 
  	ssh $SSH_USER@$node "sudo wipefs -a /dev/$device"
    done
    echo "removing /var/lib/quobyte"
    ssh $SSH_USER@$node "sudo rm -rf /var/lib/quobyte"
    echo "removing /etc/quobyte"
    ssh $SSH_USER@$node "sudo rm -rf /etc/quobyte"
}

find_public_ip() {
    local node=$1
    local public_ip=$(ssh "$SSH_USER@$node" "curl -s ifconfig.me")
    if [ -z "$public_ip" ]; then
        echo "Could not find public IP for $node."
        return 1
    fi
    echo "$public_ip"
}

# --- Main Script Execution ---

# 1. Welcome the user
welcome_dialog
checklist_dialog || exit 1

# 2. Get the list of nodes from a file
NODE_FILE=$(get_node_file)
NODES=$(cat "$NODE_FILE")
REGISTRY_STRING="registry=$(for node in $NODES; do echo -n ${node}, ; done | sed s/,$//g)"
SSH_USER=$(get_ssh_user)

if [ "$1" == "uninstall" ]; then
   for node in $NODES; do
       distro_info=$(get_distro_info "$node")
       package_manager=$(echo "$distro_info" | cut -d':' -f4)
       remove_packages "$node" "$package_manager"
       remove_state "$node" 
   done
   exit 1
fi

if [ -z "$NODES" ]; then
    whiptail --title "Error" --msgbox "The node file is empty." 10 60 
    exit 1
fi

for node in $NODES; do
    # Check connectivity
    if ! check_connectivity "$node"; then
       echo "Could not connecto to node $node, exit installation"
       exit 1
    fi
    if ! check_timesync "$node"; then
       echo "Could not find a running time sync daemon on $node, exit installation"
       exit 1
    fi
    if ! check_distrosupport "$node"; then
       echo "Found a Linux distribution not supported on $node, exit installation"
       exit 1
    fi
done

# 3. Process each node
first_node_flag=true
for node in $NODES; do
    echo "Processing node: $node"


    # 3b. Find out distribution and version
    distro_info=$(get_distro_info "$node")
    package_manager=$(echo "$distro_info" | cut -d':' -f4)
    # 3c. Install software sources list
    install_repo "$node" "$distro_info"
    if [ -z "$package_manager" ]; then
        continue
    fi

    # 3d. Install packages
    if ! install_packages "$node" "$package_manager"; then
        continue
    fi
    
    # 3e. Quobyte bootstrap and cluster join
    if $first_node_flag; then
        echo "Bootstrapping Quobyte cluster on $node..."
        # Your Quobyte bootstrap command here
        ssh "$SSH_USER@$node" "sudo mkdir -p /var/lib/quobyte/devices/registry-data"
        ssh "$SSH_USER@$node" "sudo /usr/bin/qbootstrap -y -d /var/lib/quobyte/devices/registry-data" 2>&1 >> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo chown -R quobyte:quobyte /var/lib/quobyte"
        ssh "$SSH_USER@$node" "sudo sed -i s/^registry.*/${REGISTRY_STRING}/g  /etc/quobyte/host.cfg"
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-registry"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-registry"		>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-api"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-api"		>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-webconsole"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-webconsole"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-data"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-data"		>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-metadata"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-metadata"		>> $INSTALL_LOG
        
        # Find public IP of the bootstrapped node
        PUBLIC_IP=$(find_public_ip "$node")
        if [ -n "$PUBLIC_IP" ]; then
            first_node_flag=false
        else
            echo "Could not get public IP for the first node. Cannot continue."
            exit 1
        fi
        
    else
        echo "Joining $node to the bootstrapped cluster..."
        # Your Quobyte cluster join command here
        ssh "$SSH_USER@$node" "sudo mkdir -p /var/lib/quobyte/devices/registry-data"
        ssh "$SSH_USER@$node" "sudo /usr/bin/qmkdev -t REGISTRY -d /var/lib/quobyte/devices/registry-data" >> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo chown -R quobyte:quobyte /var/lib/quobyte"
        ssh "$SSH_USER@$node" "sudo sed -i s/^registry.*/${REGISTRY_STRING}/g  /etc/quobyte/host.cfg"
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-registry"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-registry"		>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-api"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-api"		>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-webconsole"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-webconsole"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-data"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-data"		>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl enable --quiet quobyte-metadata"	>> $INSTALL_LOG
        ssh "$SSH_USER@$node" "sudo systemctl restart quobyte-metadata"		>> $INSTALL_LOG
    fi
done

# 4. Final welcome message
if [ -n "$PUBLIC_IP" ]; then
    whiptail --title "Installation Complete" --msgbox "Congratulations! The Quobyte cluster has been installed. Please open your web browser and navigate to:\n\nhttp://$PUBLIC_IP:8080\n\nto complete the setup." 15 70
else
    whiptail --title "Installation Failed" --msgbox "The installation could not be completed. Please check the logs for errors." 15 70
fi


