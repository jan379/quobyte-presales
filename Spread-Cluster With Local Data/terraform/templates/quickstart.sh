#!/usr/bin/env bash

until ls provisioning/inventory.yaml; do 
  sleep 5; 
  echo "Waiting for cloud-init to be finished..."
done ; 
cp ansible-vars provisioning/vars/ansible-vars
cp ansible-inventory.yaml provisioning/inventory.yaml
cd provisioning
ansible-playbook -i inventory.yaml 00_install_quobyte_server.yaml 01_setup_coreservices.yaml 02_create_superuser.yaml 03_add_metadataservices.yaml 04_add_dataservices.yaml 05_optional_tune-cluster.yaml 06_optional_install_defaultclient.yaml 07_optional_license_cluster.yaml
