#!/bin/bash

# A simple Quobyte installer script using whiptail for dialog-based interaction.

# --- Configuration Variables ---
QUOBYTE_REPO_URL="https://packages.quobyte.com/repo/current"
PACKAGE_NAMES="quobyte-server quobyte-tools"
SSH_USER="jan"
# For passwordless SSH, you'd use a key. For a password, you might use 'sshpass' or similar.
# This script assumes SSH keys are in place for security.

# --- Function Definitions ---

welcome_dialog() {
    whiptail --title "Quobyte Installer" --msgbox "Welcome to the Quobyte software installer! This script will guide you through the process of setting up a new Quobyte cluster." 10 60
}

get_ssh_user() {
    SSH_USER=$(whiptail --title "Quobyte Installer" --inputbox "Please enter the user name to connect via SSH to the target nodes." 10 60 3>&1 1>&2 2>&3)
    echo "${SSH_USER}"
}

get_node_file() {
    NODE_FILE=$(whiptail --title "Quobyte Installer" --inputbox "Please enter the full path to the file containing your install target nodes, one per line:" 10 60 3>&1 1>&2 2>&3)
    
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

get_distro_info() {
    local node=$1
    local distro=$(ssh "$SSH_USER@$node" 'source /etc/os-release && echo "$ID"')
    local version=$(ssh "$SSH_USER@$node" 'source /etc/os-release && echo "$VERSION_ID"')
    local major_version=$(echo ${version} | awk -F\. '{print $1'})
    echo "$distro:$version:$major_version"
}

install_repo() {
    local node=$1
    local distro_info=$2
    local distro=$(echo "$distro_info" | cut -d':' -f1)
    local version=$(echo "$distro_info" | cut -d':' -f2)
    local major_version=$(echo "$distro_info" | cut -d':' -f3)
    case "$distro" in
        rocky|almalinux|centos)
            local quobyte_distro_alias="RockyLinux"
            ;;
        *)
            echo "Unsupported distribution: $distro"
            return 1
            ;;
    esac

    echo "Installing Quobyte repository on $node ($distro $version)..."
    
    REPO_URL=""
    PACKAGE_MANAGER=""

    case "$distro" in
        rocky|almalinux|centos)
            REPO_URL="${QUOBYTE_REPO_URL}/rpm/${quobyte_distro_alias}_${major_version}/"
            PACKAGE_MANAGER="dnf"
            ssh "$SSH_USER@$node" "sudo dnf config-manager --add-repo ${REPO_URL}quobyte.repo"
            ;;
        ubuntu|debian)
            REPO_URL="${QUOBYTE_REPO_URL}/deb/${distro^}_${version}/"
            PACKAGE_MANAGER="apt"
            ssh "$SSH_USER@$node" "sudo sh -c 'echo \"deb ${REPO_URL} /\" > /etc/apt/sources.list.d/quobyte.list' && sudo apt-get update"
            ;;
        *)
            echo "Unsupported distribution: $distro"
            return 1
            ;;
    esac
    
    if [ $? -ne 0 ]; then
        echo "Failed to install repository on $node."
        return 1
    fi

    echo "Repository installed successfully."
    echo "$PACKAGE_MANAGER"
}

install_packages() {
    local node=$1
    local pkg_manager=$2

    echo "Installing packages on $node using package manager ${pgk_manager}..."
    
    if [ "$pkg_manager" == "dnf" ] || [ "$pkg_manager" == "yum" ]; then
        ssh "$SSH_USER@$node" "sudo $pkg_manager install -y $PACKAGE_NAMES"
    elif [ "$pkg_manager" == "apt" ]; then
        ssh "$SSH_USER@$node" "sudo apt-get install -y $PACKAGE_NAMES"
    else
        echo "Unknown package manager ${pkg_manager}."
        return 1
    fi
    
    if [ $? -ne 0 ]; then
        echo "Failed to install packages on $node."
        return 1
    fi

    echo "Packages installed successfully."
    return 0
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

# 2. Get the list of nodes from a file
NODE_FILE=$(get_node_file)
NODES=$(cat "$NODE_FILE")
if [ -z "$NODES" ]; then
    whiptail --title "Error" --msgbox "The node file is empty." 10 60 
    exit 1
fi

SSH_USER=$(get_ssh_user)

# 3. Process each node
first_node_flag=true
for node in $NODES; do
    echo "Processing node: $node"

    # 3a. Check connectivity
    if ! check_connectivity "$node"; then
        continue # Skip to the next node if this one fails
    fi

    # 3b. Find out distribution and version
    DISTRO_INFO=$(get_distro_info "$node")

    # 3c. Install software sources list
    PKG_MANAGER=$(install_repo "$node" "$DISTRO_INFO" | tail -n 1)
    if [ -z "$PKG_MANAGER" ]; then
        continue
    fi

    # 3d. Install packages
    if ! install_packages "$node" "$PKG_MANAGER"; then
        continue
    fi
    
    # 3e. Quobyte bootstrap and cluster join
    if $first_node_flag; then
        echo "Bootstrapping Quobyte cluster on $node..."
        # Your Quobyte bootstrap command here
        # Example: ssh "$SSH_USER@$node" "sudo quobyte-bootstrap-command --init"
        
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
        # Example: ssh "$SSH_USER@$node" "sudo quobyte-join-command --cluster-ip $PUBLIC_IP"
    fi
done

# 4. Final welcome message
if [ -n "$PUBLIC_IP" ]; then
    whiptail --title "Installation Complete" --msgbox "Congratulations! The Quobyte cluster has been installed. Please open your web browser and navigate to:\n\nhttps://$PUBLIC_IP:8080\n\nto complete the setup." 15 70
else
    whiptail --title "Installation Failed" --msgbox "The installation could not be completed. Please check the logs for errors." 15 70
fi



