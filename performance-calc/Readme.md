# Usage

You can write down infrastructure variables in a file, see "default.ini" as an example. 
You can change asptects as used Erasure Code, Replication striping width but also 
use device throughput limits, NIC capacity etc. as input variable.

Disclaimer: This script displays theoretical upper boundaries, i.e. what is to expect under ideal 
conditions. So rather an indication, but certainly something you should come close to when benchmarking 
in real life.

Simply invoke the python script + your hardware configuration: 

```
$ ./calc.py -c defaultconfig.ini 

## Capacity:
Cluster raw capacity: 244.8 TB
Cluster EC capacity: 153.0 TB
Cluster replication capacity: 81.6 TB

## Device performance:
Single Node device throughput: 96.11 GiB/s
Single Node device controller throughput: 2.79 GiB/s
Cluster wide device throughput write: 576.67 GiB/s
Cluster wide device throughput read: 938.77 GiB/s
Cluster wide controller throughput: 16.76 GiB/s

## Network performance:
Single storage node network throughput: 2.91 GiB/s
Single client node network throughput: 2.91 GiB/s
Storage cluster network throughput: 17.46 GiB/s
Client cluster network throughput: 5.82 GiB/s

## Erasure Coding:
Single client write, EC
EC single write bottleneck: client_network
EC single write performance, 2 threads per client: 1.82 GiB/s

Single client read, EC
EC single write bottleneck: client_network
EC single write performance, 2 threads per client: 2.91 GiB/s

Multi client write, Erasure Coding
EC multi write bottleneck: client_network
EC multi write performance, 2 threads per client: 3.64 GiB/s

Multi client read, Erasure Coding
EC multi read bottleneck: client_network
EC multi read performance, 2 threads per client: 5.82 GiB/s

## Replication:
Single client write, Replication
Replication single write bottleneck: client_network
Replicated single write performance, 2 threads per client: 2.91 GiB/s

Single client read, Replication
Replication single read bottleneck: client_network
Replicated single read performance, 2 threads per client: 2.91 GiB/s

Multi client write, Replication
Replication multi client write bottleneck: backend_controller_limit
Replicated multi write performance, 2 threads per client: 5.59 GiB/s

Multi client read, Replication
Replication multi client read bottleneck: client_network
Replicated multi read performance, 2 threads per client: 5.82 GiB/s

## No Redundancy:
Multi client write, no replication
Multi client write bottleneck, unreplicated: client_network
Unreplicated multi write performance, 2 threads per client: 5.82 GiB/s

Multi client read, no replication
Multi client read bottleneck, unreplicated: client_network
Unreplicated multi read performance, 2 threads per client: 5.82 GiB/s

Single client write, no replication
Single client write bottleneck, unreplicated: client_network
Unreplicated single write performance, 2 threads per client: 2.91 GiB/s

Single client read, no replication
Single client read bottleneck, unreplicated: client_network
Unreplicated single read performance, 2 threads per client: 2.91 GiB/s

```

