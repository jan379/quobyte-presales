#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install -y wget ansible git
# Get Quobyte Ansible playbooks
git clone git@github.com/quobyte/quobyte-ansible.git
# Get presales playbooks
git clone git@github.com:jan379/quobyte-presales.git
git config --global user.email "jan.peschke@quobyte.com"
git config --global user.name "Jan Peschke"

# Let's start with a valid license right from the beginning
grep "fill in a valid Quobyte license key" ansible-vars && exit 1
cp ansible-vars quobyte-ansible/vars/ansible-vars
cp ansible-inventory.yaml quobyte-ansible/inventory.yaml
cd quobyte-ansible 
ansible-playbook -i inventory.yaml 00_install_quobyte_server.yaml 01_setup_coreservices.yaml 02_create_superuser.yaml 03_add_metadataservices.yaml 04_add_dataservices.yaml 05_optional_tune-cluster.yaml 06_optional_install_defaultclient.yaml 07_optional_license_cluster.yaml
