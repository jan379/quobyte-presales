#!/usr/bin/env bash

# Ask for storage node list

whiptail --title "Welcome to Quobyte!" --msgbox "Welcome to the Quobyte preflight check. \n \
 This script will allow to create an Ansible inventory plus set \n \
 all necessary vairables needed to install Quobyte on a set of \n \
 given nodes." 10 78

# Ask for client node list
if (whiptail --title "Storage Nodes" --yesno "Do you have a text file containing all storage nodes, one per line?" 8 78); then
    echo "User selected Yes, exit status was $?."
    NODE_LIST=$(whiptail --inputbox "Path to your text file containing all storage nodes:" 8 39 Blue --title "Storage Nodes" 3>&1 1>&2 2>&3)
                                                                        # A trick to swap stdout and stderr.
    # Again, you can pack this inside if, but it seems really long for some 80-col terminal users.
    exitstatus=$?
    if [ $exitstatus = 0 ]; then
         echo "User selected Ok and entered " $NODE_LIST
    else
        echo "User selected Cancel."
    fi

    echo "(Exit status was $exitstatus)"
else
    echo "User selected No, exit status was $?."
fi

# Ask for username to use for any remote connection

# Prepare inventory

# Prepare variables

# Check storage node for metadata devices

#
