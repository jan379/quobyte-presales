#!/usr/bin/env python3

import sys
import getopt
import configparser

argv = sys.argv[1:]
try:
    options, args = getopt.getopt(argv, "c:", ["configfile="])
except:
    print(err)
for name, value in options:
    if name in ['-c', '--configfile']:
        configfile = value
    else:
        configfile = 'default.ini'

config = configparser.ConfigParser()
try: 
    config.read(configfile)
except:
    print("could not read configfile %s" % (configfile))

client_nic_gbs = float(config.get('clients', 'capacity_nic_gbs'))
client_nic_mbs = float(client_nic_gbs*1024)
number_clients = int(config.get('clients', 'number_clients'))

storagenode_nic_gbs = float(config.get('storagenodes', 'capacity_nic_gbs'))
storagenode_nic_mbs = float(storagenode_nic_gbs * 1024)
number_storagenodes = int(config.get('storagenodes', 'number_nodes'))
number_storagenode_devices = int(config.get('storagenodes', 'number_devices'))
device_throughput_mbs = int(config.get('storagenodes', 'device_throughput_mbs'))
device_capacity_GB = int(config.get('storagenodes', 'capacity_devices_GB'))

ec_datastripes = int(config.get('storageconfig', 'ec_datastripes'))  
ec_codingstripes = int(config.get('storageconfig', 'ec_codingstripes'))  


# Replication stripe width is influencing performance
replication_stripewidth = int(config.get('storageconfig', 'replication_stripewidth')) 
# Data redundancy when using replication. 1 = unreplicated, 3 = default, 5 = paranoid but doable
replication_factor = int(config.get('storageconfig', 'replication_factor')) 

# Sustained device throughput per storagenode
host_throughput_device_mbs = number_storagenode_devices * device_throughput_mbs

# Sustained device throughput clusterwide
cluster_throughput_device_mbs = host_throughput_device_mbs * number_storagenodes

# Overall cluster raw capacity, raw
cluster_capacity_raw_GB = round(number_storagenodes*number_storagenode_devices*device_capacity_GB, 2)
cluster_capacity_raw_TB = round(cluster_capacity_raw_GB / 1024, 2)
cluster_capacity_raw_PB = round(cluster_capacity_raw_TB / 1024, 2)

# Overall cluster raw capacity, replicated
cluster_capacity_repl_GB = round((cluster_capacity_raw_GB)/3, 2)
cluster_capacity_repl_TB = round(cluster_capacity_repl_GB / 1024, 2)
cluster_capacity_repl_PB = round(cluster_capacity_repl_TB / 1024, 2)

# Overall cluster raw capacity, EC 
cluster_capacity_ec_GB = round((cluster_capacity_raw_GB)/((ec_datastripes+ec_codingstripes)/ec_datastripes), 2)
cluster_capacity_ec_TB = round(cluster_capacity_ec_GB / 1024, 2)
cluster_capacity_ec_PB = round(cluster_capacity_ec_TB / 1024, 2)

# Device performance
# One upper throughput boundary is the overall device throughput capacity
cluster_device_throughput_capacity = number_storagenodes * number_storagenode_devices * device_throughput_mbs

# Network backend capacity
# One upper throughput boundary is the overall storage network throughput capacity
cluster_network_throughput_capacity = number_storagenodes * storagenode_nic_mbs

# Network frontend capacity
# One upper throughput boundary is the overall client network throughput capacity
client_network_throughput_capacity = number_clients * client_nic_mbs 

# Single client performance
## One client can write one stripe as fast as one storage device can write (sustained).
## If you use more stripes (EC or repl. + stripe_width > 1), you can multiply write throughput.
## Placement algorithm will try to place data as distributed as possible, i.e. a file with 3x replication and 
## stripe_width 2 will be distributed across devices on 6 nodes. Frontend and replication traffic will not interfere 
## on such a cluster. But if a cluster is smaller (< replication factor * stripe_width), frontend traffic and replication 
## traffic will share the same network interface. As a consequence this NIC can become a bottleneck.

# Replication
## A single client replication is limited by client_nic_mbs.
## A single client replication is limited by cluster_device_throughput_capacity minus replication_device_throughput_requirements 
replication_device_throughput_requirements = ((cluster_device_throughput_capacity / 3) * 2)
cluster_device_replication_capacity = cluster_device_throughput_capacity - replication_device_throughput_requirements
## A single client replication is limited by cluster_network_throughput_capacity minus replication_network_throughput_requirements. 
replication_network_throughput_requirements = ((cluster_network_throughput_capacity / 3) * 2)
cluster_network_replication_capacity = cluster_network_throughput_capacity - replication_network_throughput_requirements
## A single client replication has the expected throughput of "device_throughput_mbs * replication_stripewidth".
single_client_replicated_striped = device_throughput_mbs * replication_stripewidth
single_client_write_throughput_replicated_mbs = min(client_nic_mbs, cluster_device_replication_capacity, cluster_network_replication_capacity, single_client_replicated_striped)
single_client_write_throughput_replicated_MBs = round(single_client_write_throughput_replicated_mbs / 8, 2)

# Erasure Coding
## A single client EC is limited by client host network capacity minus coding_stripe_bandwidth.
## That is (client_nic_mbs / (ec_datastripes + ec_codingstripes)) * ec_datastripes), 
## A single client EC is limited by cluster_network_throughput_capacity.
## A single client EC is limited by cluster_device_throughput_capacity.
## A single  client EC has the expected throughput of "device_throughput_mbs * data stripe count"

print("")
print("# Welcome!")
print("")
print("Your storage cluster consists of %s storagenodes." % number_storagenodes)
print("")
print("## Capacity")
print("")
print("### Capacity RAW:")
print("%s GB\t | %s TB\t | %s PB" % (cluster_capacity_raw_GB, cluster_capacity_raw_TB, cluster_capacity_raw_PB))
print("")
print("### Capacity usable ( EC %s+%s):" % (ec_datastripes,ec_codingstripes))
print("%s GB\t | %s TB\t | %s PB" % (cluster_capacity_ec_GB, cluster_capacity_ec_TB, cluster_capacity_ec_PB))
print("")
print("### Capacity usable (3x replicated):")
print("%s GB\t | %s TB\t | %s PB" % (cluster_capacity_repl_GB, cluster_capacity_repl_TB, cluster_capacity_repl_PB))
print("")

print("")
print("## Performance")
print("")
print("### Theoretical max. single client/ single stream performance (data stored 3x replicated):")
print("%s MB/s" % (single_client_write_throughput_replicated_MBs))
print("")
print("### Theoretical max. multi client performance:")
print("")
