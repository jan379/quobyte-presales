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

## EC code to use. 
ec_codingstripes=3
ec_datastripes=5

## Replication stripe width
replication_stripewidth=1

## Sustained device throughput per storagenode
host_throughput_device_mbs=number_storagenode_devices*device_throughput_mbs

## Sustained device throughput clusterwide
cluster_throughput_device_mbs=number_storagenode_devices*device_throughput_mbs*number_storagenodes

print("Welcome!")
