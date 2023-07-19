#!/usr/bin/env bash

# Qualified resiliency:
# Will the system recover autonomously after stopping cluster impact?

# Quantified resiliency: 
# How low can we get this value while I/O is still running?
clusterquality=40

controllplane=$(qmgmt service list | grep Metadata | awk '{print $1}')

for i in $(seq 120); do
  for host in $controllplane; do
    ssh $host "sudo pkill -9 java"
    sleep $clusterquality
  done
done
