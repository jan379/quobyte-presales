# One dataservice per CPU socket?

## Idea: Run multiple dataservices on multi socket systems 

To avoid latencies introduced by inter-cpu traffic the idea is 
to use one dataservice per CPU socket.

This dataservice serves NVMe mapped to that socket.
This dataservice listens on the interface mapped to that socket.

To start different data services with different config files the respective 
systemd unit needs to set the current working directory to a specific path.
Config files can be placed in that path.
 
## Ingredients

### Listen-IP / interface

It will be necessary that one dataservice only registers the interface(s) that are "near". I.e. if the service serves NVMe of numa zone 6 or 7 it should use the interface(s) that are part of that numa zone.
The relevant config parameters are:
rpc.bind_address = and
http.bind_address =
They can be set to an IPv4 address of that interface.

### NVMe partitioning

We will neeed different XFS labels for NVMe in different NUMA zones. 
Dataservices will need to have that label configured to pick up the right devices.

### NUMA CPUAffinity setting

Services will need a CPUAffinity= setting applied in their unit files.
Are NUMAPolicy or NUMAMask settings needed?

Optional: post_sequence tuning script

### resources:
CPU affinity
https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/8/html/managing_monitoring_and_updating_the_kernel/assembly_configuring-cpu-affinity-and-numa-policies-using-systemd_managing-monitoring-and-updating-the-kernel 

RDMA error codes
https://enterprise-support.nvidia.com/s/article/understanding-mlx5-linux-counters-and-status-parameters#jive_content_id_Counter_Groups
