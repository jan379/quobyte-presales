#!/usr/bin/env python3

import sys
import json
import argparse 
import configparser

# Global variables we need
config = configparser.ConfigParser()

# Helper functions

def get_megabit_to_megabyte(mbval):
    return (mbval/8)

def get_megabit_to_gigabit(mbval):
    return round((mbval / 1000),2)

def get_megabit_to_mebibyte(mbval):
    return round((mbval / 8.388608),2)

# Return capacity in gigabytes using a nice unit/ suffix
def get_pretty_capacity(capacity_gb):
    if capacity_gb > 1000*1000:
        return("%s PB" % str(round(capacity_gb / 1000 / 1000, 2)))
    elif capacity_gb > 1000 and capacity_gb < 1000*1000:
        return("%s TB" % str(round(capacity_gb / 1000, 2)))
    else:
        return("%s GB" % str(round(capacity_gb, 2)))

# Return a tuple of performance value, rounded to two digits and a matching unit
def get_pretty_performance(performance_mbs):
    performance_mebibyte = get_megabit_to_mebibyte(performance_mbs)
    if performance_mebibyte < 1024:
        performance_unit = "MiB/s"
        performance_value = performance_mebibyte 
    elif performance_mebibyte >= 1024 and performance_mebibyte < 1024 * 1024:
        performance_unit = "GiB/s"
        performance_value = performance_mebibyte / 1024 
    elif performance_mebibyte >= 1024 * 1024 and performance_mebibyte < 1024 * 1024 * 1024:
        performance_unit = "TiB/s" 
        performance_value = performance_mebibyte / 1024 / 1024
    else:
        performance_unit = "not implemented" 
        performance_value = performance_mebibyte / 1024 / 1024
    return (round(performance_value, 2), performance_unit)

# Calculate usable capacity from raw for EC
def get_raw_to_usable_ec(raw, datastripes, codingstripes):
    return((raw)/((datastripes + codingstripes) / datastripes))

# Calculate usable capacity from raw for replication 
def get_raw_to_usable_repl(raw, replication_factor):
    return((raw)/replication_factor)

# Calculate raw cluster capacity
def get_cluster_capacity_raw_gb(number_storagenodes, number_devices, device_capacity):
    return round(number_storagenodes * number_devices * device_capacity_GB, 2)

## Sustained device throughput per storagenode
def get_host_throughput_device(number_devices, device_throughput):
    return number_devices * device_throughput

## Summed up device controller throughput per storagenode
def get_host_throughput_controller(number_controllers, throughput):
    return number_controllers * throughput
    
## Sustained device throughput clusterwide
def get_cluster_throughput_device(number_storagenodes, host_throughput_device):
    return number_storagenodes * host_throughput_device
    
## Summed up controller throughput for all storage nodes 
def get_cluster_throughput_controller(number_storagenodes, host_throughput_controller):
    return number_storagenodes * host_throughput_controller
    
# Cluster line rate network throughput
def get_cluster_throughput_network(number_nodes, host_throughput_network):
    return round(float(number_nodes * host_throughput_network),2 )

# Single client EC writes
## A single client EC is limited by host network capacity minus EC frontend overhead .
## A single client EC is limited by cluster_network_throughput_capacity.
## A single client EC is limited by cluster_device_throughput_capacity.
## A single client EC is limited by cluster_controller_throughput_capacity.
## A single  client EC has the expected throughput of "device_throughput_mbs * data stripe count * client_threads"
def get_single_client_ec_writes_mbs(client_nic_mbs, client_threads, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, ec_datastripes, ec_codingstripes):
    single_client_mbs = (device_throughput_mbs * ec_datastripes * client_threads)
    single_client_ec_frontend_network_limit = (client_nic_mbs / (ec_datastripes + ec_codingstripes)) * ec_datastripes
    ec_cluster_network_limit = (cluster_throughput_network / (ec_datastripes + ec_codingstripes)) * ec_datastripes
    ec_cluster_device_throughput_limit = (cluster_throughput_device / (ec_datastripes + ec_codingstripes)) * ec_datastripes
    ec_cluster_controller_throughput_limit = (cluster_throughput_controller / (ec_datastripes + ec_codingstripes)) * ec_datastripes
    bottleneck_tuple =  min((single_client_ec_frontend_network_limit, 'client_network'), (single_client_mbs, 'ec_writes'), (ec_cluster_controller_throughput_limit, 'storage_network'),(ec_cluster_device_throughput_limit, 'backend_device_limit'),(ec_cluster_controller_throughput_limit, 'backend_controller'))
    return bottleneck_tuple

# Single client EC reads
## A single client EC read is limited by host network capacity.
## A single client EC read is limited by cluster_network_throughput_capacity.
## A single client EC read is limited by cluster_device_throughput_capacity.
## A single client EC read is limited by cluster_controller_throughput_capacity.
## A single  client EC has the expected throughput of "device_throughput_mbs * data stripe count * client_threads"
def get_single_client_ec_reads_mbs(client_nic_mbs, client_threads, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, ec_datastripes, ec_codingstripes):
    single_client_mbs = (device_throughput_mbs * ec_datastripes * client_threads)
    single_client_ec_frontend_network_limit = client_nic_mbs
    ec_cluster_network_limit = cluster_throughput_network
    ec_cluster_device_throughput_limit = cluster_throughput_device
    ec_cluster_controller_throughput_limit = cluster_throughput_controller
    bottleneck_tuple =  min((single_client_ec_frontend_network_limit, 'client_network'), (single_client_mbs, 'ec_writes'), (ec_cluster_controller_throughput_limit, 'storage_network'),(ec_cluster_device_throughput_limit, 'backend_device_limit'),(ec_cluster_controller_throughput_limit, 'backend_controller'))
    return bottleneck_tuple

# Single client replication writes
## A single client replication write is limited by client_node_network_capacity.
## A single client replication write is limited by cluster_network_throughput_capacity / replication_factor.
## A single client replication write is limited by cluster_device_throughput_capacity / replication_factor.
## A single client replication write is limited by cluster_controller_throughput_capacity / replication_factor.
## A single client replication read has the expected throughput of "device_throughput_mbs * stripe_width * client_threads"
def get_single_client_repl_writes_mbs(client_nic_mbs, client_threads, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, replication_factor, replication_stripewidth):
    single_client_mbs = (device_throughput_mbs * replication_stripewidth * client_threads)
    single_client_frontend_network_limit = (client_nic_mbs)
    single_client_backend_network_limit = (cluster_throughput_network / replication_factor)
    single_client_backend_device_limit = (cluster_throughput_device / replication_factor)
    single_client_backend_controller_limit = (cluster_throughput_controller / replication_factor)
    bottleneck_tuple =  min((single_client_frontend_network_limit, 'client_network'), (single_client_mbs, 'replicated_writes'), (single_client_backend_network_limit, 'storage_network'), (single_client_backend_device_limit, 'backend_device_limit'), (single_client_backend_controller_limit, 'backend_controller'))
    return bottleneck_tuple

#  Single client replication read
## A single client replication read is limited by client_node_network_capacity.
## A single client replication read is limited by cluster_network_throughput_capacity.
## A single client replication read is limited by cluster_device_throughput_capacity.
## A single client replication read is limited by cluster_controller_throughput_capacity.
## A single client replication read has the expected throughput of "device_throughput_mbs * stripe_width * client_threads"
def get_single_client_repl_reads_mbs(client_nic_mbs, client_threads, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, replication_factor, replication_stripewidth):
    single_client_mbs = (device_throughput_mbs * replication_stripewidth * client_threads)
    single_client_frontend_network_limit = client_nic_mbs
    single_client_backend_network_limit = cluster_throughput_network
    single_client_backend_device_limit = cluster_throughput_device
    single_client_backend_controller_limit = cluster_throughput_controller
    bottleneck_tuple =  min((single_client_frontend_network_limit, 'client_network'), (single_client_mbs, 'replicated_reads'), (single_client_backend_network_limit, 'storage_network'), (single_client_backend_device_limit, 'backend_device_limit'), (single_client_backend_controller_limit, 'backend_controller'))
    return bottleneck_tuple

#  Single client unreplicated read/ write
## Single client unreplicated I/O is limited by client_node_network_capacity.
## Single client unreplicated I/O is limited by cluster_network_throughput_capacity.
## Single client unreplicated I/O is limited by cluster_device_throughput_capacity.
## Single client unreplicated I/O is limited by cluster_controller_throughput_capacity.
## Single client unreplicated I/O has the expected throughput of "device_throughput_mbs * stripe_width * client_threads"
def get_single_client_unrepl_readwrite_mbs(client_nic_mbs, client_threads, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, replication_stripewidth):
    single_client_mbs = (device_throughput_mbs * replication_stripewidth * client_threads)
    single_client_frontend_network_limit = client_nic_mbs
    single_client_backend_network_limit = cluster_throughput_network
    single_client_backend_device_limit = cluster_throughput_device
    single_client_backend_controller_limit = cluster_throughput_controller
    bottleneck_tuple =  min((single_client_frontend_network_limit, 'client_network'), (single_client_mbs, 'unreplicated_readwrite'), (single_client_backend_network_limit, 'storage_network'), (single_client_backend_device_limit, 'backend_device_limit'), (single_client_backend_controller_limit, 'backend_controller'))
    return bottleneck_tuple

#  Multi client, multi stream reads/writes, unreplicated
## Multi client unreplicated performance is limited by client_network_throughput_capacity
## Multi client unreplicated is limited by cluster_network_replication_capacity
## Multi client unreplicated is limited by cluster_device_replication_capacity
## Multi client unreplicated is limited by cluster_controller_replication_capacity
## Multi client unreplicated expected throughput is number_clients * device_throughput_mbs
def get_multi_client_unrepl_readwrite_mbs(number_clients, client_threads, client_throughput_network, cluster_throughput_device, cluster_throughput_network, cluster_throughput_controller, replication_stripewidth):
	multi_client_unreplicated_striped_mbs = number_clients * device_throughput_mbs * replication_stripewidth * client_threads
	unreplicated_cluster_network_limit = cluster_throughput_network
	unreplicated_cluster_device_throughput_limit = cluster_throughput_device
	unreplicated_cluster_controller_throughput_limit = cluster_throughput_controller
	bottleneck_tuple = min((multi_client_unreplicated_striped_mbs, 'unreplicated_writes'), (client_throughput_network, 'client_network'), (unreplicated_cluster_network_limit, 'storage_network'), (unreplicated_cluster_device_throughput_limit, 'backend_device_limit'), (unreplicated_cluster_controller_throughput_limit, 'backend_controller_limit'))
	return bottleneck_tuple

#  Multi client, multi stream writes, replicated
## Multi client replicated write performance is limited by client_network_throughput_capacity
## Multi client replicated write performance is limited by cluster_network_capacity / replication_factor
## Multi client replicated write performance is limited by cluster_device_throughput_capacity /replication_factor
## Multi client replicated write performance is limited by cluster_controller_throughput_capacity / replication_factor
## Multi client replicated expected throughput is number_clients * client_threads device_throughput_mbs * replication_stripewidth
def get_multi_client_repl_writes_mbs(number_clients, client_threads, client_throughput_network, cluster_throughput_device, cluster_throughput_network, cluster_throughput_controller, replication_factor, replication_stripewidth):
	multi_client_replicated_striped_mbs = number_clients * device_throughput_mbs * replication_stripewidth * client_threads
	replicated_client_network_limit = client_throughput_network
	replicated_cluster_network_limit = cluster_throughput_network / replication_factor
	replicated_cluster_device_throughput_limit = cluster_throughput_device / replication_factor
	replicated_cluster_controller_throughput_limit = cluster_throughput_controller / replication_factor
	bottleneck_tuple = min((multi_client_replicated_striped_mbs, 'replicated_writes'), (replicated_client_network_limit, 'client_network'), (replicated_cluster_network_limit, 'storage_network'), (replicated_cluster_device_throughput_limit, 'backend_device_limit'), (replicated_cluster_controller_throughput_limit, 'backend_controller_limit'))
	return bottleneck_tuple

#  Multi client, multi stream read, replicated
## Multi client replicated read performance is limited by client_network_throughput_capacity
## Multi client replicated read performance is limited by cluster_network_capacity
## Multi client replicated read performance is limited by cluster_device_throughput_capacity
## Multi client replicated read performance is limited by cluster_controller_throughput_capacity
## Multi client replicated read expected throughput is number_clients * client_threads * device_throughput_mbs * replication_stripewidth
def get_multi_client_repl_reads_mbs(number_clients, client_threads, client_throughput_network, cluster_throughput_device, cluster_throughput_network, cluster_throughput_controller, replication_factor, replication_stripewidth):
	multi_client_replicated_striped_mbs = number_clients * device_throughput_mbs * replication_stripewidth * client_threads
	replicated_client_network_limit = client_throughput_network
	replicated_cluster_network_limit = cluster_throughput_network
	replicated_cluster_device_throughput_limit = cluster_throughput_device
	replicated_cluster_controller_throughput_limit = cluster_throughput_controller
	bottleneck_tuple = min((multi_client_replicated_striped_mbs, 'replicated_writes'), (replicated_client_network_limit, 'client_network'), (replicated_cluster_network_limit, 'storage_network'), (replicated_cluster_device_throughput_limit, 'backend_device_limit'), (replicated_cluster_controller_throughput_limit, 'backend_controller_limit'))
	return bottleneck_tuple

#  Multi client, multi stream write performance, EC 
## Multi client EC is limited by frontend network capacity minus coding_stripe_bandwidth.
## Multi client EC is limited by cluster_network_throughput_capacity.
## Multi client EC is limited by cluster_device_throughput_capacity.
## Multi client EC is limited by cluster_controller_throughput_capacity.
## Multi client EC has the expected throughput of "device_throughput_mbs * data stripe count * number_clients"
def get_multi_client_ec_writes_mbs(number_clients, client_threads, client_throughput_network, cluster_throughput_device, cluster_throughput_network, cluster_throughput_controller, ec_datastripes, ec_codingstripes):
	multi_client_ec_striped_mbs = number_clients * device_throughput_mbs * ec_datastripes * client_threads
	ec_client_network_limit = (client_throughput_network / (ec_datastripes + ec_codingstripes)) * ec_datastripes
	ec_cluster_network_limit = (cluster_throughput_network / (ec_datastripes + ec_codingstripes)) * ec_datastripes
	ec_cluster_device_throughput_limit = (cluster_throughput_device / (ec_datastripes + ec_codingstripes)) * ec_datastripes
	ec_cluster_controller_throughput_limit = (cluster_throughput_controller / (ec_datastripes + ec_codingstripes)) * ec_datastripes
	bottleneck_tuple = min((multi_client_ec_striped_mbs, 'ec_writes'), (ec_client_network_limit, 'client_network'), (ec_cluster_network_limit, 'storage_network'), (ec_cluster_device_throughput_limit, 'backend_device_limit'), (ec_cluster_controller_throughput_limit, 'backend_controller_limit'))
	return bottleneck_tuple

#  Multi client, multi stream read performance, EC 
## Multi client EC is limited by frontend network
## Multi client EC is limited by cluster_network_throughput_capacity.
## Multi client EC is limited by cluster_device_throughput_capacity.
## Multi client EC is limited by cluster_controller_throughput_capacity.
## Multi client EC has the expected throughput of "device_throughput_mbs * data stripe count * number_clients"
def get_multi_client_ec_reads_mbs(number_clients, client_threads, client_throughput_network, cluster_throughput_device_read, cluster_throughput_network, cluster_throughput_controller, ec_datastripes, ec_codingstripes):
	multi_client_ec_striped_mbs = number_clients * device_throughput_mbs * ec_datastripes * client_threads
	ec_client_network_limit = client_throughput_network
	ec_cluster_network_limit = cluster_throughput_network
	ec_cluster_device_throughput_limit = cluster_throughput_device_read * ec_datastripes
	ec_cluster_controller_throughput_limit = cluster_throughput_controller
	bottleneck_tuple = min((multi_client_ec_striped_mbs, 'ec_reads'), (ec_client_network_limit, 'client_network'), (ec_cluster_network_limit, 'storage_network'), (ec_cluster_device_throughput_limit, 'backend_device_limit'), (ec_cluster_controller_throughput_limit, 'backend_controller_limit'))
	return bottleneck_tuple

# See if we can open/ read a config file
def get_configfile():
    global output_format
    parser = argparse.ArgumentParser(
        description='Calculate Capacity and Performance for given hardware configurations.',
        epilog='Provide your own config file ("./calc-ng.py -c myconfig.ini")')
    
    parser.add_argument('-c', '--configfile')
    parser.add_argument('-f', '--format', default="text")
    
    args = parser.parse_args()
    
    if(args.configfile == None):
        print("No configuration file provided.")
        print(parser.epilog)
        raise SystemExit(1)
    if(args.format == "json"):
        output_format = "json"
    else:
        output_format = "text"

    #print()
    #print("Using configuration file: %s" % args.configfile)
    #print("Output format: %s" % output_format)
    
    # Check if configfile is readable
    try:
        f = open(args.configfile, 'r')
    except OSError:
        print("Cannot open", args.configfile)
        raise SystemExit(1)
    else:
        f.close
    
    try: 
        config.read(args.configfile)
    except:
        print("Could not read configfile %s" % args.configfile)

# Read configuration values and use them as global variables. 
def read_configvalues():
    ## Client section
    global number_clients 
    global client_threads # how many parallel threads will the application use? 
    global client_nic_gbs 
    global client_nic_mbs 
    ## Storage nodes
    global storagenode_nic_gbs 
    global storagenode_nic_mbs 
    global number_storagenodes 
    global number_storagenode_devices 
    global device_throughput_mbs 
    global device_throughput_mbs_read 
    global controller_throughput_mbs 
    global number_storagenode_device_controller
    global device_capacity_GB 
    # Quobyte configuration
    global ec_datastripes 
    global ec_codingstripes 
    global replication_stripewidth 
    global replication_factor 

    number_clients = int(config.get('clients', 'number_clients', fallback=1))
    client_threads = int(config.get('clients', 'number_threads', fallback=1))
    client_nic_gbs = float(config.get('clients', 'capacity_nic_gbs', fallback=1.0))
    
    storagenode_nic_gbs = float(config.get('storagenodes', 'capacity_nic_gbs', fallback=1.0))
    number_storagenodes = int(config.get('storagenodes', 'number_nodes', fallback=1))
    number_storagenode_devices = int(config.get('storagenodes', 'number_devices', fallback=1))
    number_storagenode_device_controller = int(config.get('storagenodes', 'number_device_controller', fallback=1))
    device_throughput_mbs = int(config.get('storagenodes', 'device_throughput_mbs', fallback=100))
    device_throughput_mbs_read = int(config.get('storagenodes', 'device_throughput_mbs_read', fallback=100))
    controller_throughput_mbs = int(config.get('storagenodes', 'controller_throughput_mbs', fallback=24000))
    device_capacity_GB = int(config.get('storagenodes', 'capacity_devices_GB', fallback=100))
    ec_datastripes = int(config.get('storageconfig', 'ec_datastripes', fallback=5))  
    ec_codingstripes = int(config.get('storageconfig', 'ec_codingstripes', fallback=3))  
    
    replication_stripewidth = int(config.get('storageconfig', 'replication_stripewidth', fallback=1)) 
    replication_factor = int(config.get('storageconfig', 'replication_factor', fallback=3)) 
    

# Check configfile
get_configfile()
# Read config values
read_configvalues()

# Calculate capacity for RAW, EC, Replication
cluster_capacity_raw = get_cluster_capacity_raw_gb(number_storagenodes, number_storagenode_devices, device_capacity_GB)
cluster_capacity_ec = get_raw_to_usable_ec(cluster_capacity_raw, ec_datastripes, ec_codingstripes)
cluster_capacity_repl = get_raw_to_usable_repl(cluster_capacity_raw, replication_factor)

# Calculate device throughput limits
node_throughput_device = get_host_throughput_device(number_storagenode_devices, device_throughput_mbs)
node_throughput_device_read = get_host_throughput_device(number_storagenode_devices, device_throughput_mbs_read) 
node_throughput_controller = get_host_throughput_controller(number_storagenode_device_controller, controller_throughput_mbs)
cluster_throughput_device = get_cluster_throughput_device(number_storagenodes, node_throughput_device)
cluster_throughput_device_read = get_cluster_throughput_device(number_storagenodes, node_throughput_device_read)
cluster_throughput_controller = get_cluster_throughput_controller(number_storagenodes, node_throughput_controller)
# pretty units, pretty numbers
pretty_node_throughput_device = get_pretty_performance(node_throughput_device)
pretty_node_throughput_device_read = get_pretty_performance(node_throughput_device_read)
pretty_node_throughput_controller = get_pretty_performance(node_throughput_controller)
pretty_cluster_throughput_device = get_pretty_performance(cluster_throughput_device)
pretty_cluster_throughput_device_read = get_pretty_performance(cluster_throughput_device_read)
pretty_cluster_throughput_controller = get_pretty_performance(cluster_throughput_controller)

# Calculate network throughput limits
storagenode_nic_mbs = storagenode_nic_gbs * 1000
client_nic_mbs = client_nic_gbs * 1000
storage_cluster_throughput_network = get_cluster_throughput_network(number_storagenodes, storagenode_nic_gbs)
client_cluster_throughput_network  = get_cluster_throughput_network(number_clients, client_nic_gbs)
storage_cluster_throughput_network_mbs = storage_cluster_throughput_network * 1000
client_cluster_throughput_network_mbs  = client_cluster_throughput_network  * 1000
# pretty units, pretty numbers
pretty_storagenode_nic_mbs = get_pretty_performance(storagenode_nic_mbs) 
pretty_client_nic_mbs = get_pretty_performance(client_nic_mbs)
pretty_storage_cluster_throughput_network = get_pretty_performance(storage_cluster_throughput_network_mbs)
pretty_client_cluster_throughput_network = get_pretty_performance(client_cluster_throughput_network_mbs)

# Calculate single client Erasure Coding writes
single_write_ec   = get_single_client_ec_writes_mbs(client_nic_mbs, client_threads, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, ec_datastripes, ec_codingstripes)
pretty_single_write_ec = get_pretty_performance(single_write_ec[0])

# Calculate single client Erasure Coding reads 
single_read_ec   = get_single_client_ec_reads_mbs(client_nic_mbs, client_threads, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, ec_datastripes, ec_codingstripes)
pretty_single_read_ec = get_pretty_performance(single_read_ec[0])

# Calculate single client replicated writes
single_write_repl = get_single_client_repl_writes_mbs(client_nic_mbs, client_threads, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, replication_factor, replication_stripewidth)
pretty_single_write_repl = get_pretty_performance(single_write_repl[0])

# Calculate single client replicated reads
single_read_repl = get_single_client_repl_reads_mbs(client_nic_mbs, client_threads, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, replication_factor, replication_stripewidth)
pretty_single_read_repl = get_pretty_performance(single_read_repl[0])

# Calculate single client unreplicated reads
single_read_unrepl = get_single_client_unrepl_readwrite_mbs(client_nic_mbs, client_threads, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, replication_stripewidth)
pretty_single_read_unrepl = get_pretty_performance(single_read_unrepl[0])

# Calculate single client unreplicated writes
single_write_unrepl = get_single_client_unrepl_readwrite_mbs(client_nic_mbs, client_threads, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, replication_stripewidth)
pretty_single_write_unrepl = get_pretty_performance(single_write_unrepl[0])

# Calculate multi client unreplicated reads/ writes. They are the same, but... let's assign the variables
multi_read_unrepl = get_multi_client_unrepl_readwrite_mbs(number_clients, client_threads, client_cluster_throughput_network_mbs, cluster_throughput_device, storage_cluster_throughput_network_mbs, cluster_throughput_controller, replication_stripewidth)
pretty_multi_read_unrepl = get_pretty_performance(multi_read_unrepl[0])
multi_write_unrepl = get_multi_client_unrepl_readwrite_mbs(number_clients, client_threads, client_cluster_throughput_network_mbs, cluster_throughput_device, storage_cluster_throughput_network_mbs, cluster_throughput_controller, replication_stripewidth)
pretty_multi_write_unrepl = get_pretty_performance(multi_write_unrepl[0])

# Calculate multi client replicated writes
multi_write_repl = get_multi_client_repl_writes_mbs(number_clients, client_threads, client_cluster_throughput_network_mbs, cluster_throughput_device, storage_cluster_throughput_network_mbs, cluster_throughput_controller, replication_factor, replication_stripewidth)
pretty_multi_write_repl = get_pretty_performance(multi_write_repl[0])

# Calculate multi client replicated reads
multi_read_repl = get_multi_client_repl_reads_mbs(number_clients, client_threads, client_cluster_throughput_network_mbs, cluster_throughput_device, storage_cluster_throughput_network_mbs, cluster_throughput_controller, replication_factor, replication_stripewidth)
pretty_multi_read_repl = get_pretty_performance(multi_read_repl[0])

# Calculate multi client Erasure Coding writes
multi_write_ec = get_multi_client_ec_writes_mbs(number_clients, client_threads, client_cluster_throughput_network_mbs, cluster_throughput_device, storage_cluster_throughput_network_mbs, cluster_throughput_controller, ec_datastripes, ec_codingstripes)
pretty_multi_write_ec = get_pretty_performance(multi_write_ec[0])

# Calculate multi client Erasure Coding reads
multi_read_ec = get_multi_client_ec_reads_mbs(number_clients, client_threads, client_cluster_throughput_network_mbs, cluster_throughput_device_read, storage_cluster_throughput_network_mbs, cluster_throughput_controller, ec_datastripes, ec_codingstripes)
pretty_multi_read_ec = get_pretty_performance(multi_read_ec[0])

# WIP, all data in one dictionary
mycluster = {
        # Client specs
	"client_count": number_clients,
	"client_threads": client_threads,
        "single_clientnode_network_throughput": {"value": pretty_client_nic_mbs[0], "unit": pretty_client_nic_mbs[1]},
        # Capacity
        "capacity_raw":get_pretty_capacity(cluster_capacity_raw),
        "capacity_ec":get_pretty_capacity(cluster_capacity_ec),
        "capacity_repl":get_pretty_capacity(cluster_capacity_repl),
        # Single Node Performance
        "single_node_device_throughput": {"value": pretty_node_throughput_device[0], "unit": pretty_node_throughput_device[1]},
        "single_node_controller_throughput": {"value": pretty_node_throughput_controller[0], "unit": pretty_node_throughput_controller[1]},
        "single_node_network_throughput": {"value": pretty_storagenode_nic_mbs[0], "unit": pretty_storagenode_nic_mbs[1]},
        # Cluster Device Performance
        "aggregated_device_throughput_write": {"value": pretty_cluster_throughput_device[0], "unit": pretty_cluster_throughput_device[1]},
        "aggregated_device_throughput_read": {"value": pretty_cluster_throughput_device_read[0], "unit": pretty_cluster_throughput_device_read[1]}, 
        "aggregated_controller_throughput": {"value": pretty_cluster_throughput_controller[0], "unit": pretty_cluster_throughput_controller[1]},
        # Cluster Network Performance
        "aggregated_network_throughput": {"value": pretty_storage_cluster_throughput_network[0], "unit": pretty_storage_cluster_throughput_network[1]},
        "aggregated_client_network_throughput": {"value": pretty_client_cluster_throughput_network[0], "unit": pretty_client_cluster_throughput_network[1]},
	# Computed throughput values
	## EC
	"ec_single_write_bottleneck": single_write_ec[1],
	"ec_single_write_throughput": {"value": pretty_single_write_ec[0], "unit": pretty_single_write_ec[1]},
	"ec_single_read_bottleneck": single_read_ec[1],
	"ec_single_read_throughput": {"value": pretty_single_read_ec[0], "unit": pretty_single_read_ec[1]},
	"ec_multi_write_bottleneck": multi_write_ec[1],
	"ec_multi_write_throughput": {"value": pretty_multi_write_ec[0], "unit": pretty_multi_write_ec[1]},
	"ec_multi_read_bottleneck": multi_read_ec[1],
	"repl_multi_read_throughput": {"value": pretty_multi_read_repl[0], "unit": pretty_multi_read_repl[1]},
	## Replicated
	"repl_single_write_bottleneck": single_write_repl[1],
	"repl_single_write_throughput": {"value": pretty_single_write_repl[0], "unit": pretty_single_write_repl[1]},
	"repl_single_read_bottleneck": single_read_repl[1],
	"repl_single_read_throughput": {"value": pretty_single_read_repl[0], "unit": pretty_single_read_repl[1]},
	"repl_multi_write_bottleneck": multi_write_repl[1],
	"repl_multi_write_throughput": {"value": pretty_multi_write_repl[0], "unit": pretty_multi_write_repl[1]},
	"repl_multi_read_bottleneck": multi_read_repl[1],
	"repl_multi_read_throughput": {"value": pretty_multi_read_repl[0], "unit": pretty_multi_read_repl[1]},
	## Unreplicated
	"unrepl_single_write_bottleneck": single_write_unrepl[1],
	"unrepl_single_write_throughput": {"value": pretty_single_write_unrepl[0], "unit": pretty_single_write_unrepl[1]},
	"unrepl_single_read_bottleneck": single_read_unrepl[1],
	"unrepl_single_read_throughput": {"value": pretty_single_read_unrepl[0], "unit": pretty_single_read_unrepl[1]},
	"unrepl_multi_write_bottleneck": multi_write_unrepl[1],
	"unrepl_multi_write_throughput": {"value": pretty_multi_write_unrepl[0], "unit": pretty_multi_write_unrepl[1]},
	"unrepl_multi_read_bottleneck": multi_read_unrepl[1],
	"unrepl_multi_read_throughput": {"value": pretty_multi_read_unrepl[0], "unit": pretty_multi_read_unrepl[1]},
	"empty": "value"
    }

## Output
def print_text():
	print()
	print("## Capacity:")
	print("Cluster raw capacity: %s" % mycluster["capacity_raw"])
	print("Cluster EC capacity: %s" % mycluster["capacity_ec"])
	print("Cluster replication capacity: %s" % mycluster["capacity_repl"])
	print()
	print("## Device performance:")
	print("Single Node device throughput: %s %s" % (mycluster["single_node_device_throughput"]["value"], mycluster["single_node_device_throughput"]["unit"]))
	print("Single Node device controller throughput: %s %s" % (mycluster["single_node_controller_throughput"]["value"],mycluster["single_node_controller_throughput"]["unit"]))
	print("Cluster wide device throughput write: %s %s" % (mycluster["aggregated_device_throughput_write"]["value"], mycluster["aggregated_device_throughput_write"]["unit"]))
	print("Cluster wide device throughput read: %s %s" % (mycluster["aggregated_device_throughput_read"]["value"], mycluster["aggregated_device_throughput_read"]["unit"]))
	print("Cluster wide controller throughput: %s %s" % (mycluster["aggregated_controller_throughput"]["value"], mycluster["aggregated_controller_throughput"]["unit"]))
	print()
	print("## Network performance:")
	print("Single storage node network throughput: %s %s" % (mycluster["single_node_network_throughput"]["value"], mycluster["single_node_network_throughput"]["unit"]))
	print("Single client node network throughput: %s %s" % (mycluster["single_clientnode_network_throughput"]["value"], mycluster["single_clientnode_network_throughput"]["unit"]))
	print("Storage cluster network throughput: %s %s" % (mycluster["aggregated_network_throughput"]["value"], mycluster["aggregated_network_throughput"]["unit"]))
	print("Client cluster network throughput: %s %s" % (mycluster["aggregated_client_network_throughput"]["value"], mycluster["aggregated_client_network_throughput"]["unit"]))
	print()
	print("## Erasure Coding:")
	print("Single client write, EC")
	print("EC single write bottleneck: %s" % single_write_ec[1])
	print("EC single write performance, %s threads per client: %s %s" % (client_threads, pretty_single_write_ec[0], pretty_single_write_ec[1]))
	print()
	print("Single client read, EC")
	print("EC single write bottleneck: %s" % single_read_ec[1])
	print("EC single write performance, %s threads per client: %s %s" % (client_threads, pretty_single_read_ec[0], pretty_single_read_ec[1]))
	print()
	print("Multi client write, Erasure Coding")
	print("EC multi write bottleneck: %s" % multi_write_ec[1])
	print("EC multi write performance, %s threads per client: %s %s" % (client_threads, pretty_multi_write_ec[0], pretty_multi_write_ec[1]))
	print()
	print("Multi client read, Erasure Coding")
	print("EC multi read bottleneck: %s" % multi_read_ec[1])
	print("EC multi read performance, %s threads per client: %s %s" % (client_threads, pretty_multi_read_ec[0], pretty_multi_read_ec[1]))
	print()
	print("## Replication:")
	print("Single client write, Replication")
	print("Replication single write bottleneck: %s" % single_write_repl[1])
	print("Replicated single write performance, %s threads per client: %s %s" % (client_threads, pretty_single_read_repl[0], pretty_single_read_repl[1]))
	print()
	print("Single client read, Replication")
	print("Replication single read bottleneck: %s" % single_write_repl[1])
	print("Replicated single read performance, %s threads per client: %s %s" % (client_threads, pretty_single_read_repl[0], pretty_single_read_repl[1]))
	print()
	print("Multi client write, Replication")
	print("Replication multi client write bottleneck: %s" % multi_write_repl[1])
	print("Replicated multi write performance, %s threads per client: %s %s" % (client_threads, pretty_multi_write_repl[0], pretty_multi_write_repl[1]))
	print()
	print("Multi client read, Replication")
	print("Replication multi client read bottleneck: %s" % multi_read_repl[1])
	print("Replicated multi read performance, %s threads per client: %s %s" % (client_threads, pretty_multi_read_repl[0], pretty_multi_read_repl[1]))
	print()
	print("## No Redundancy:")
	print("Multi client write, no replication")
	print("Multi client write bottleneck, unreplicated: %s" % multi_write_unrepl[1])
	print("Unreplicated multi write performance, %s threads per client: %s %s" % (client_threads, pretty_multi_read_unrepl[0], pretty_multi_write_unrepl[1]))
	print()
	print("Multi client read, no replication")
	print("Multi client read bottleneck, unreplicated: %s" % multi_read_unrepl[1])
	print("Unreplicated multi read performance, %s threads per client: %s %s" % (client_threads, pretty_multi_read_unrepl[0], pretty_multi_read_unrepl[1]))
	print()
	print("Single client write, no replication")
	print("Single client write bottleneck, unreplicated: %s" % single_write_unrepl[1])
	print("Unreplicated single write performance, %s threads per client: %s %s" % (client_threads, pretty_single_write_unrepl[0], pretty_single_write_unrepl[1]))
	print()
	print("Single client read, no replication")
	print("Single client read bottleneck, unreplicated: %s" % single_read_unrepl[1])
	print("Unreplicated single read performance, %s threads per client: %s %s" % (client_threads, pretty_single_read_unrepl[0], pretty_single_read_unrepl[1]))
	print()
	
def print_json():
    myjson = json.dumps(mycluster)
    print(myjson)

if(output_format == "json"):
    print_json()
else:
    print_text()
