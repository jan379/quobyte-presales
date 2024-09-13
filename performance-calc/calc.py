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

# Sustained device throughput per storagenode
host_throughput_device_mbs = number_storagenode_devices*device_throughput_mbs

# Sustained device throughput clusterwide
cluster_throughput_device_mbs = number_storagenode_devices*device_throughput_mbs*number_storagenodes

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


print("")
print("# Welcome!")
print("")
print("Your storage cluster consists of %s storagenodes." % number_storagenodes)
print("")
print("## Capacity")
print("")
print("### Capacity RAW:")
print("%sGB\t | %sTB\t | %sPB" % (cluster_capacity_raw_GB, cluster_capacity_raw_TB, cluster_capacity_raw_PB))
print("")
print("### Capacity usable ( EC %s+%s):" % (ec_datastripes,ec_codingstripes))
print("%sGB\t | %sTB\t | %sPB" % (cluster_capacity_ec_GB, cluster_capacity_ec_TB, cluster_capacity_ec_PB))
print("")
print("### Capacity usable (3x replicated):")
print("%sGB\t | %sTB\t | %sPB" % (cluster_capacity_repl_GB, cluster_capacity_repl_TB, cluster_capacity_repl_PB))
print("")

