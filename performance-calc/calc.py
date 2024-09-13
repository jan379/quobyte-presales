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

# Single client performance
## One client can write one stripe as fast as one storage device can write (sustained).
## If you use more stripes (EC or repl. + stripe_width > 1), you can multiply write thoughput.
## Stripe width should not be larger than number_storagenodes.
## Replication traffic needs 2/3 of available backend network capacity, so it will max out at that value.
## A single client will never be faster than client_nic_gbs.
## A single client is also limited by overall device throughput. 
replication_inputstream = device_throughput_mbs * replication_stripewidth
# We will need two times the ingress bandwidth on a storage node for replication/ egress traffic
replication_bandwidth = replication_inputstream * 2
# We will be limited by outbound traffic from first dataservice to two replicas, because our 
# replica sets should be written to other machines / failure domains.
replication_limit = storagenode_nic_mbs / replication_bandwidth
# We will have 1/3 of device throughput capacity available when using 3 x replication
replication_cluster_throughput_capacity = round(cluster_device_throughput_capacity / 3)
single_client_write_throughput_replicated_mbs = min(replication_inputstream, client_nic_mbs, replication_cluster_throughput_capacity, replication_limit)
single_client_write_throughput_replicated_MBs = round(single_client_write_throughput_replicated_mbs / 8, 2)


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

print("")
print("## Performance")
print("")
print("### Theoretical max. single client performance (MByte/s):")
print(single_client_write_throughput_replicated_MBs)
print("")
print("### Theoretical max. multi client performance:")
print("")
