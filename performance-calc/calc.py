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
client_nic_mbs = float(client_nic_gbs*1000)
number_clients = int(config.get('clients', 'number_clients'))

storagenode_nic_gbs = float(config.get('storagenodes', 'capacity_nic_gbs'))
storagenode_nic_mbs = float(storagenode_nic_gbs * 1000)
number_storagenodes = int(config.get('storagenodes', 'number_nodes'))
number_storagenode_devices = int(config.get('storagenodes', 'number_devices'))
device_throughput_mbs = int(config.get('storagenodes', 'device_throughput_mbs'))
device_capacity_GB = int(config.get('storagenodes', 'capacity_devices_GB'))

ec_datastripes = int(config.get('storageconfig', 'ec_datastripes'))  
ec_codingstripes = int(config.get('storageconfig', 'ec_codingstripes'))  


# Replication stripe width is influencing performance
replication_stripewidth = int(config.get('storageconfig', 'replication_stripewidth')) 
# Data redundancy when using replication. 1 = unreplicated, 3 = default, 5 = paranoid
replication_factor = int(config.get('storageconfig', 'replication_factor')) 

# Sustained device throughput per storagenode
host_throughput_device_mbs = number_storagenode_devices * device_throughput_mbs

# Sustained device throughput clusterwide
cluster_throughput_device_mbs = host_throughput_device_mbs * number_storagenodes

# Overall cluster raw capacity, raw
cluster_capacity_raw_GB = round(number_storagenodes*number_storagenode_devices*device_capacity_GB, 2)
cluster_capacity_raw_TB = round(cluster_capacity_raw_GB / 1000, 2)
cluster_capacity_raw_PB = round(cluster_capacity_raw_TB / 1000, 2)

# Overall cluster raw capacity, replicated
cluster_capacity_repl_GB = round((cluster_capacity_raw_GB)/replication_factor, 2)
cluster_capacity_repl_TB = round(cluster_capacity_repl_GB / 1000, 2)
cluster_capacity_repl_PB = round(cluster_capacity_repl_TB / 1000, 2)

# Overall cluster raw capacity, EC 
cluster_capacity_ec_GB = round((cluster_capacity_raw_GB)/((ec_datastripes+ec_codingstripes)/ec_datastripes), 2)
cluster_capacity_ec_TB = round(cluster_capacity_ec_GB / 1000, 2)
cluster_capacity_ec_PB = round(cluster_capacity_ec_TB / 1000, 2)

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
## A single client replicated is limited by client_nic_mbs.
## A single client replicated is limited by cluster_device_throughput_capacity minus replication_device_throughput_overhead 
replication_device_throughput_overhead = ((cluster_device_throughput_capacity / replication_factor) * (replication_factor -1 ))
cluster_device_replication_capacity = cluster_device_throughput_capacity - replication_device_throughput_overhead
## A single client replication is limited by cluster_network_throughput_capacity minus replication_network_throughput_overhead. 
replication_network_throughput_overhead = ((cluster_network_throughput_capacity / replication_factor) * (replication_factor - 1))
cluster_network_replication_capacity = cluster_network_throughput_capacity - replication_network_throughput_overhead
## A single client replication has the expected throughput of "device_throughput_mbs * replication_stripewidth".
single_client_replicated_striped = device_throughput_mbs * replication_stripewidth
single_client_write_throughput_replicated_mbs = min(client_nic_mbs, cluster_device_replication_capacity, cluster_network_replication_capacity, single_client_replicated_striped)
single_client_write_throughput_replicated_MBs = round(single_client_write_throughput_replicated_mbs / 8, 2)
# get the name of the bottleneck
single_client_write_throughput_replicated_mbs_dict = {
        client_nic_mbs: "client network interface bandwidth. Adding frontend network capabilities will increase performance.", 
        cluster_device_replication_capacity: "storage device bandwidth including replication penalty. Adding more (or faster) storage devices will increase performance.", 
        cluster_network_replication_capacity: "storage network including replication penalty. Adding more backend network capabilities will increase performance.", 
        single_client_replicated_striped: "device performance, including striping factor. Using faster devices or a broader stripe_width will increase performance."
        }
single_client_replicated_bottleneck_val = min(single_client_write_throughput_replicated_mbs_dict)
single_client_replicated_bottleneck_key = (single_client_write_throughput_replicated_mbs_dict[single_client_replicated_bottleneck_val])

# Erasure Coding
## A single client EC is limited by client host network capacity minus coding_stripe_bandwidth.
single_client_ec_frontend_network_overhead = (client_nic_mbs / (ec_datastripes + ec_codingstripes)) * (ec_codingstripes)
single_client_ec_frontend_capacity = client_nic_mbs - single_client_ec_frontend_network_overhead
## A single client EC is limited by cluster_network_throughput_capacity.
## A single client EC is limited by cluster_device_throughput_capacity.
## A single  client EC has the expected throughput of "device_throughput_mbs * data stripe count"
single_client_ec = device_throughput_mbs * ec_datastripes 
single_client_write_throughput_ec_mbs = min(single_client_ec_frontend_capacity, cluster_network_throughput_capacity, cluster_device_throughput_capacity, single_client_ec)
single_client_write_throughput_ec_MBs = round(single_client_write_throughput_ec_mbs / 8, 2)
# get the name of the bottleneck
single_client_write_throughput_ec_mbs_dict = {
        single_client_ec_frontend_capacity: "client network interface bandwidth, including EC overhead. Adding frontend network capabilities will increase performance.", 
        cluster_device_throughput_capacity: "total storage device throughput capacity. Adding storage devices will increase performance.", 
        cluster_network_throughput_capacity: "total storage network capacity. Adding backend network capabilities will increase performance.", 
        single_client_ec: "the performance of all data stripes written by a single client. Using faster devices or more data stripes will increase performance."
        }
single_client_ec_bottleneck_val = min(single_client_write_throughput_ec_mbs_dict)
single_client_ec_bottleneck_key = (single_client_write_throughput_ec_mbs_dict[single_client_ec_bottleneck_val])

# Single Client, multi stream performance
## maybe later
# Multi client, single stream performance
## maybe later

# Multi client, multi stream performance, replicated
## Multi client replicated performance is limited by client_network_throughput_capacity
## Multi client replicated is limited by cluster_network_replication_capacity
## Multi client replicated is limited by cluster_device_replication_capacity
## Multi client replicated expected throughput is number_clients * device_throughput_mbs * replication_stripewidth
multi_client_replicated_striped = number_clients * device_throughput_mbs * replication_stripewidth
multi_client_write_throughput_replicated_mbs = min(client_network_throughput_capacity, cluster_device_replication_capacity, cluster_network_replication_capacity, multi_client_replicated_striped)
multi_client_write_throughput_replicated_MBs = round(multi_client_write_throughput_replicated_mbs / 8, 2)
# get the name of the bottleneck
multi_client_write_throughput_replicated_mbs_dict = {
        client_network_throughput_capacity: "total client network interface bandwidth. Adding frontend network capabilities will increase performance.", 
        cluster_device_replication_capacity: "total storage device throughput, including replication penalty. Adding more storage devices will increase performance.", 
        cluster_network_replication_capacity: "total storage network bandwidth, including replication penalty. Adding backend network capabilities will increase performance.", 
        multi_client_replicated_striped: "device throughput of devices clients write to, including striping. Using more clients or more stripes will increase performance."
        }
multi_client_replicated_bottleneck_val = min(multi_client_write_throughput_replicated_mbs_dict)
multi_client_replicated_bottleneck_key = (multi_client_write_throughput_replicated_mbs_dict[multi_client_replicated_bottleneck_val])

# Multi client, multi stream performance, unreplicated
## Multi client unreplicated performance is limited by client_network_throughput_capacity
## Multi client unreplicated is limited by cluster_network_throughput_capacity
## Multi client unreplicated is limited by cluster_device_throughput_capacity
## Multi client unreplicated expected throughput is number_clients * device_throughput_mbs * replication_stripewidth
multi_client_unreplicated_striped = number_clients * device_throughput_mbs * replication_stripewidth
multi_client_write_throughput_unreplicated_mbs = min(client_network_throughput_capacity, cluster_device_throughput_capacity, cluster_network_throughput_capacity, multi_client_unreplicated_striped)
multi_client_write_throughput_unreplicated_MBs = round(multi_client_write_throughput_unreplicated_mbs / 8, 2)
# get the name of the bottleneck
multi_client_write_throughput_unreplicated_mbs_dict = {
        client_network_throughput_capacity: "total client network bandwidth. Adding frontend network capabilities will increase performance.", 
        cluster_device_throughput_capacity: "total storage device throughput. Adding more storage devices will increase performance.", 
        cluster_network_throughput_capacity: "total storage network bandwidth, including replication penalty. Adding backend network capabilities will increase performance.", 
        multi_client_unreplicated_striped: "device throughput of devices clients write to, including striping. Using more clients or broader stripe_width will increase performance"
        }
multi_client_unreplicated_bottleneck_val = min(multi_client_write_throughput_unreplicated_mbs_dict)
multi_client_unreplicated_bottleneck_key = (multi_client_write_throughput_unreplicated_mbs_dict[multi_client_unreplicated_bottleneck_val])

# Multi client, multi stream performance, EC 
## Multi client EC is limited by frontend network capacity minus coding_stripe_bandwidth.
multi_client_ec_frontend_capacity = single_client_ec_frontend_capacity * number_clients
## Multi client EC is limited by cluster_network_throughput_capacity.
## Multi client EC is limited by cluster_device_throughput_capacity.
## Multi client EC has the expected throughput of "device_throughput_mbs * data stripe count * number_clients"
multi_client_ec = device_throughput_mbs * ec_datastripes * number_clients
multi_client_write_throughput_ec_mbs = min(multi_client_ec_frontend_capacity, cluster_network_throughput_capacity, cluster_device_throughput_capacity, multi_client_ec)
multi_client_write_throughput_ec_MBs = round(multi_client_write_throughput_ec_mbs / 8, 2)
# get the name of the bottleneck
multi_client_write_throughput_ec_mbs_dict = {
        multi_client_ec_frontend_capacity: "total client network bandwidth, including EC overhead. Adding frontend network capabilities will increase performance.", 
        cluster_device_throughput_capacity: "total storage device throughput capacity. Adding storage devices will increase performance.", 
        cluster_network_throughput_capacity: "total storage network capacity. Adding backend network capabilities will increase performance.", 
        multi_client_ec: "the performance of all data stripes written by all clients. Using faster devices or more data stripes will increase performance."
        }
multi_client_ec_bottleneck_val = min(multi_client_write_throughput_ec_mbs_dict)
multi_client_ec_bottleneck_key = (multi_client_write_throughput_ec_mbs_dict[multi_client_ec_bottleneck_val])


print("")
print("# Welcome!")
print("")
print("Your storage cluster consists of:")
print("%s\tstorage nodes" % (number_storagenodes))
print("%s\tclient nodes"  % (number_clients))
print("")
print("## Capacity")
print("")
print("| Redundancy                      \t| GB      \t| TB      \t| PB       \t|")
print("| ------------------------------- \t| ------- \t| ------- \t| -------- \t|")
print("| Capacity RAW\t                  \t| %s   \t| %s   \t| %s    \t|" % (cluster_capacity_raw_GB, cluster_capacity_raw_TB, cluster_capacity_raw_PB))
print("| Capacity usable (EC %s+%s)      \t| %s   \t| %s   \t| %s    \t|" % (ec_datastripes,ec_codingstripes, cluster_capacity_ec_GB, cluster_capacity_ec_TB, cluster_capacity_ec_PB))
print("| Capacity usable (Replicated %sx)\t| %s   \t| %s   \t| %s    \t|" % (replication_factor,cluster_capacity_repl_GB, cluster_capacity_repl_TB, cluster_capacity_repl_PB))
print("")

print("## Performance")
print("")
print("### Theoretical max. single client/ single stream performance data stored %sx replicated, stripe_width %s):" % (replication_factor, replication_stripewidth))
print("%s MB/s" % (single_client_write_throughput_replicated_MBs))
print("The upper limit is determined by %s" % (single_client_replicated_bottleneck_key))
print("")
print("### Theoretical max. multi client/ multi stream performance data stored %sx replicated, stripe_width %s, %s clients):" % (replication_factor, replication_stripewidth, number_clients))
print("%s MB/s" % (multi_client_write_throughput_replicated_MBs))
print("The upper limit is determined by %s" % (multi_client_replicated_bottleneck_key))
print("")
print("### Theoretical max. multi client/ multi stream performance data stored unreplicated, stripe_width %s, %s clients):" % (replication_stripewidth, number_clients))
print("%s MB/s" % (multi_client_write_throughput_unreplicated_MBs))
print("The upper limit is determined by %s" % (multi_client_unreplicated_bottleneck_key))
print("")

print("### Theoretical max. single client/ single stream performance (data stored EC%s+%s):" % (ec_datastripes, ec_codingstripes))
print("%s MB/s" % (single_client_write_throughput_ec_MBs))
print("The upper limit is determined by %s" % (single_client_ec_bottleneck_key))
print("")
print("### Theoretical max. multi client/ multi stream performance (data stored EC%s+%s), %s clients:" % (ec_datastripes, ec_codingstripes, number_clients))
print("%s MB/s" % (multi_client_write_throughput_ec_MBs))
print("The upper limit is determined by %s" % (multi_client_ec_bottleneck_key))
print("")
