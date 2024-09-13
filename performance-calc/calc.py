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


# Replication stripe width is influencing performance
replication_stripewidth = int(config.get('storageconfig', 'replication_stripewidth')) 

## Sustained device throughput per storagenode
host_throughput_device_mbs = number_storagenode_devices*device_throughput_mbs

## Sustained device throughput clusterwide
cluster_throughput_device_mbs = number_storagenode_devices*device_throughput_mbs*number_storagenodes

# Overall cluster raw capacity
cluster_capacity_GB = number_storagenodes*number_storagenode_devices*device_capacity_GB


print("")
print("# Welcome!")
print("")
print("Your storage cluster consists of %s storagenodes." % number_storagenodes)
print("")
print("## Capacity")
print("")
print("### RAW capacity:")
print("%s GB" % (cluster_capacity_GB))
print("")
print("### Useable capacity when using replication:")
print("%s GB" % (cluster_capacity_GB/3))
print("")
print("### Useable capacity when using erasure coding EC%s+%s:" % (ec_datastripes,ec_codingstripes))
print("%s GB" % (cluster_capacity_GB/((ec_datastripes+ec_codingstripes)/ec_datastripes)))
print("")

