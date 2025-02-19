#!/usr/bin/env python3

import sys
import argparse 
import configparser

# Global variables we need
config = configparser.ConfigParser()

# Helper functions

# [X][e,i]bibyte to [X][e,i]gabyte
# Example: Gigibyte to Gigabyte
def XiB_to_XB(xibivalue):
    return int(xibivalue * 1.074)

# [X][e,i]gabyte to [X][e,i]bibyte
# Example: Gigabyte to Gigibyte
def XB_to_XiB(xigavalue):
    return (xigavalue / 1.074)

def megabit_to_megabyte(mbval):
    return (mbval/8)

def megabit_to_gigabit(mbval):
    return round((mbval / 1000),2)

# Return capacity in gigabytes using a nice unit/ suffix
def pretty_capacity(capacity_gb):
    if capacity_gb > 1000*1000:
        return("%s PB" % str(round(capacity_gb / 1000 / 1000, 2)))
    elif capacity_gb > 1000 and capacity_gb < 1000*1000:
        return("%s TB" % str(round(capacity_gb / 1000, 2)))
    else:
        return("%s GB" % str(round(capacity_gb, 2)))

# Calculate usable capacity from raw for EC
def raw_to_usable_ec(raw, datastripes, codingstripes):
    return((raw)/((datastripes + codingstripes) / datastripes))

# Calculate usable capacity from raw for replication 
def raw_to_usable_repl(raw, replication_factor):
    return((raw)/replication_factor)

# Calculate raw cluster capacity
def cluster_capacity_raw_gb(number_storagenodes, number_devices, device_capacity):
    return round(number_storagenodes * number_devices * device_capacity_GB, 2)

## Sustained device throughput per storagenode
def host_throughput_device(number_devices, device_throughput):
    return number_devices * device_throughput

## Summed up device controller throughput per storagenode
def host_throughput_controller(number_controllers, throughput):
    return number_controllers * throughput
    
## Sustained device throughput clusterwide
def cluster_throughput_device(number_storagenodes, host_throughput_device):
    return number_storagenodes * host_throughput_device
    
## Summed up controller throughput for all storage nodes 
def cluster_throughput_controller(number_storagenodes, host_throughput_controller):
    return number_storagenodes * host_throughput_controller
    
# Cluster line rate network thoughput
def cluster_throughput_network(number_nodes, host_throughput_network):
    return round(float(number_nodes * host_throughput_network),2 )

# Calculate single client writes
## A single client EC is limited by host network capacity minus EC frontend overhead .
## A single client EC is limited by cluster_network_throughput_capacity.
## A single client EC is limited by cluster_device_throughput_capacity.
## A single client EC is limited by cluster_controller_throughput_capacity.
## A single  client EC has the expected throughput of "device_throughput_mbs * data stripe count"
def single_client_ec_writes_mbs(client_nic_mbs, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, ec_datastripes, ec_codingstripes):
    single_client_mbs = (device_throughput_mbs * ec_datastripes)
    single_client_ec_frontend_network_overhead = (client_nic_mbs / (ec_datastripes + ec_codingstripes)) * ec_codingstripes
    single_client_ec_frontend_capacity = client_nic_mbs - single_client_ec_frontend_network_overhead
    bottleneck_tuple =  min((single_client_ec_frontend_capacity, 'client_network'), (single_client_mbs, 'ec_writes'), (cluster_throughput_network, 'storage_network'))
    return bottleneck_tuple

## A single client replication limited by client_node_network_capacity.
## A single client replication limited by cluster_network_throughput_capacity / 3.
## A single client replication is limited by cluster_device_throughput_capacity / 3.
## A single client replication is limited by cluster_controller_throughput_capacity / 3.
## A single client replication is limited by client_.
## A single client replication has the expected throughput of "device_throughput_mbs * stripe_width"
def single_client_repl_writes_mbs(client_nic_mbs, device_throughput_mbs, cluster_throughput_network, cluster_throughput_device, cluster_throughput_controller, replication_factor, stripe_width):
    single_client_mbs = (device_throughput_mbs * stripe_width)
    single_client_frontend_network_limit = (client_nic_mbs)
    single_client_backend_network_limit = (cluster_throughput_network / replication_factor)
    single_client_backend_device_limit = (cluster_throughput_device / replication_factor)
    single_client_backend_controller_limit = (cluster_throughput_device / replication_factor)
    bottleneck_tuple =  min((single_client_frontend_network_limit, 'client_network'), (single_client_mbs, 'replicated_writes'), (single_client_backend_network_limit, 'storage_network'), (single_client_backend_device_limit, 'backend_device_limit'), (single_client_backend_controller_limit, 'backend_controller'))
    return bottleneck_tuple


# See if we can open/ read a config file
def get_configfile():
    parser = argparse.ArgumentParser(
        description='Calculate Capacity and Performance for given hardware configurations.',
        epilog='Provide your own config file ("./calc.py -c myconfig.ini")')
    
    parser.add_argument('-c', '--configfile')
    
    args = parser.parse_args()
    
    if(args.configfile == None):
        print("No configuration file provided.")
        print(parser.epilog)
        raise SystemExit(1)
    
    print()
    print("Using configuration file: %s" % args.configfile)
    
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
    global client_nic_gbs 
    global client_nic_mbs 
    global client_network_throughput_capacity_mbs 
    ## Storage nodes
    global storagenode_nic_gbs 
    global storagenode_nic_mbs 
    global number_storagenodes 
    global number_storagenode_devices 
    global device_throughput_mbs 
    global controller_throughput_mbs 
    global number_storagenode_device_controller
    global device_capacity_GB 
    global storagenode_throughput_device_mbs 
    # Quobyte configuration
    global ec_datastripes 
    global ec_codingstripes 
    global replication_stripewidth 
    global replication_factor 
    global client_nic_gbs 
    global client_nic_mbs 

    number_clients = int(config.get('clients', 'number_clients', fallback=1))
    client_nic_gbs = float(config.get('clients', 'capacity_nic_gbs', fallback=1.0))
    client_nic_mbs = float(client_nic_gbs*1000)
    
    storagenode_nic_gbs = float(config.get('storagenodes', 'capacity_nic_gbs', fallback=1.0))
    storagenode_nic_mbs = float(storagenode_nic_gbs * 1000)
    number_storagenodes = int(config.get('storagenodes', 'number_nodes', fallback=1))
    number_storagenode_devices = int(config.get('storagenodes', 'number_devices', fallback=1))
    number_storagenode_device_controller = int(config.get('storagenodes', 'number_device_controller', fallback=1))
    device_throughput_mbs = int(config.get('storagenodes', 'device_throughput_mbs', fallback=100))
    controller_throughput_mbs = int(config.get('storagenodes', 'controller_throughput_mbs', fallback=100))
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
cluster_capacity_raw = cluster_capacity_raw_gb(number_storagenodes, number_storagenode_devices, device_capacity_GB)
cluster_capacity_ec = raw_to_usable_ec(cluster_capacity_raw, ec_datastripes, ec_codingstripes)
cluster_capacity_repl = raw_to_usable_repl(cluster_capacity_raw, replication_factor)

# Calculate device throughput limits
node_throughput_device = host_throughput_device(number_storagenode_devices, device_throughput_mbs)
node_throughput_controller = host_throughput_controller(number_storagenode_device_controller, controller_throughput_mbs)
cluster_throughput_device = cluster_throughput_device(number_storagenodes, node_throughput_device)
cluster_throughput_controller = cluster_throughput_controller(number_storagenodes, node_throughput_controller)

# Calculate network throughput limits
storage_cluster_throughput_network = cluster_throughput_network(number_storagenodes, storagenode_nic_gbs)
client_cluster_throughput_network  = cluster_throughput_network(number_clients, client_nic_gbs)
storage_cluster_throughput_network_mbs = storage_cluster_throughput_network * 1000
client_cluster_throughput_network_mbs  = client_cluster_throughput_network  * 1000

# Calculate single client EC writes
single_write_ec   = single_client_ec_writes_mbs(client_nic_mbs, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, ec_datastripes, ec_codingstripes)
single_write_repl = single_client_repl_writes_mbs(client_nic_mbs, device_throughput_mbs, storage_cluster_throughput_network_mbs, cluster_throughput_device, cluster_throughput_controller, replication_factor, replication_stripewidth)

## Debug
print()
print("Capacity:")
print("Cluster raw capacity: %s" % pretty_capacity(cluster_capacity_raw))
print("Cluster EC capacity: %s" % pretty_capacity(cluster_capacity_ec))
print("Cluster replication capacity: %s" % pretty_capacity(cluster_capacity_repl))
print()
print("Device performance:")
print("Single Node device throughput: %s Gigabit/s" % megabit_to_gigabit(node_throughput_device))
print("Single Node device controller throughput: %s Gigabit/s" % megabit_to_gigabit(node_throughput_controller))
print("Cluster wide device throughput: %s Gigabit/s" % megabit_to_gigabit(cluster_throughput_device))
print("Cluster wide controller throughput: %s Gigabit/s" % megabit_to_gigabit(cluster_throughput_controller))
print()
print("Network performance:")
print("Single storage node network throughput: %s Gigabit/s" % storagenode_nic_gbs)
print("Single client node network throughput: %s Gigabit/s" % client_nic_gbs)
print("Storage cluster network throughput: %s Gigabit/s" % storage_cluster_throughput_network)
print("Client cluster network throughput: %s Gigabit/s" % client_cluster_throughput_network)
print()
print("Single client, EC")
print("EC single write bottleneck: %s" % single_write_ec[1])
print("EC single write performance: %s Megabit/s" % single_write_ec[0])
print()
print("Single client, Replication")
print("Replication single write bottleneck: %s" % single_write_repl[1])
print("Replication single write performance: %s Megabit/s" % single_write_repl[0])
print()
