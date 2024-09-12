#!/usr/bin/env python3

# Network parameters
## We assume that switches are capable of handling the
## load of each client/ server

## The interface throughput of a single storage server
backend_throughput_interfaces_gbs=25
## The interface throughput of a single client machine
frontend_throughput_interfaces_gbs=10

# Client node specifics
## The number of client machines
number_clients=2

# Server Node Specifics

## Numer of storage nodes
number_storagenodes=3
## Number of devices per node
number_storagenode_devices=24
## Sustained throughput per device Mbit/s
device_throughput_mbs=644 # 644=HDD, 3360=NVMe
device_capacity_GB=2200
cluster_capacity_GB=number_storagenodes*number_storagenode_devices*device_capacity_GB

## EC code to use. 
ec_codingstripes=3
ec_datastripes=5

## Replication stripe width
replication_stripewidth=1

## Sustained device throughput per storagenode
host_throughput_device_mbs=number_storagenode_devices*device_throughput_mbs

## Sustained device throughput clusterwide
cluster_throughput_device_mbs=number_storagenode_devices*device_throughput_mbs*number_storagenodes



print("# Welcome!")
print("")
print("Your storage cluster consists of",number_storagenodes, "storagenodes.")
print("")
print("# Capacity")
print("")
print("Useable Capacity when using replication: %sGB" % (cluster_capacity_GB/3))
print("Useable Capacity when using erasure coding EC%s+%s: %sGB" % (ec_datastripes,ec_codingstripes, (cluster_capacity_GB/((ec_datastripes+ec_codingstripes)/ec_datastripes))))
print("RAW Capacity: %sGB" % (cluster_capacity_GB))
