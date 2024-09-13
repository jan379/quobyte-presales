#!/usr/bin/env python3

import configparser

config = configparser.ConfigParser()
try: 
    config.read('defaultconfig.ini')
except:
    print("could not read configfile")

client_nic_gbs = float(config.get('clients', 'capacity_nic_gbs'))
number_clients = int(config.get('clients', 'number_clients'))

storagenode_nic_gbs = float(config.get('storagenodes', 'capacity_nic_gbs'))
number_storagenodes = int(config.get('storagenodes', 'number_nodes'))
number_storagenode_devices = int(config.get('storagenodes', 'number_devices'))
device_throughput_mbs = int(config.get('storagenodes', 'device_throughput_mbps'))
device_capacity_GB = int(config.get('storagenodes', 'capacity_devices_GB'))

ec_datastripes = int(config.get('storageconfig', 'ec_datastripes'))  
ec_codingstripes = int(config.get('storageconfig', 'ec_codingstripes'))  

replication_stripewidth = int(config.get('storageconfig', 'replication_stripewidth')) 

## Sustained device throughput per storagenode
host_throughput_device_mbs = number_storagenode_devices*device_throughput_mbs

## Sustained device throughput clusterwide
cluster_throughput_device_mbs = number_storagenode_devices*device_throughput_mbs*number_storagenodes

# Overall cluster raw capacity
cluster_capacity_GB = number_storagenodes*number_storagenode_devices*device_capacity_GB


print("# Welcome!")
print("")
print("Your storage cluster consists of",number_storagenodes, "storagenodes.")
print("")
print("# Capacity")
print("")
print("Useable Capacity when using replication: %sGB" % (cluster_capacity_GB/3))
print("Useable Capacity when using erasure coding EC%s+%s: %sGB" % (ec_datastripes,ec_codingstripes, (cluster_capacity_GB/((ec_datastripes+ec_codingstripes)/ec_datastripes))))
print("RAW Capacity: %sGB" % (cluster_capacity_GB))
