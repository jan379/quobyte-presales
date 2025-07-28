# Install io500 suite as painless as possible

* All nodes need (open)mpi installed
* The io500 binary needs to be compiled, we do that in a central quobyte volume (/quobyte/io500bin) to have it distributed and available on all clients.
* We use two different volumes (io500-data, io500-bin) to separate written data and binary, results, and config.
* One policy adjustment is mandatory: Set negative metadata cache to 0, to make mdtest succeeed.

mpirun --hostfile ~/io500/io500-clients.list /quobyte/io500-bin/io500/io500 /quobyte/io500-bin/io500.ini

# Optimize for io500

## Distribute Metadata Load
The more volumes are used, the more even load can be distributed across multiple services.
We can use the feauture to automatically translate "mkdir" calls to do a "create volume" call.
This way tests like "mdtest-hard" will work on many (short living) volumes.
A policy can be used to only match this very special workload. 

To activate that feature it is mandatory to:

1.) Create a user within the used tenant. This should be the (local) user that is used to run the io500 benchmark.
2.) This user should be tenant_admin and tenant_user of that tenant and have a primary posix group assigned.
3.) This user needs admin-keys created (for both, file system and API use).
4.) These keys should be used to authenticate the running Quobyte client against the storage system.

This can be done for example by using a postExec command in the respective systemd unit:

```
# /etc/systemd/system/quobyte-client.service.d/override.conf
[Service]
ExecStartPost=sudo -u jan qinfo set-access-key --secret kcxBPJxLWDEYQVlNIXxMQcpTB/una9mbfIg8L/cc --scope user kJTPDh9lQjI9Q8ln7nlI /quobyte
```

5.) The client needs to be started in "multi-tenant" mode. This will make sure that the tenant hierarchy is displayed at the mount point directory.

```
# /etc/quobyte/client-service.cfg 
registry=frontend.quobyte-demo.com.
mount_point=/quobyte
multi-tenant
```

6.) Once those requirements are met an "mkdir" call of that specific user is translated to a "create volume" call.

## Optimized placement for IOR-Hard

IOR-Hard requires that clients write in a coordinated way across the whole cluster. 
This requires usually a policy with "global locking" activated, which results in a 
call towards the metadata system to aquire that lock.

As an alternative the actual workload can be analyzed and data can be written/ read
according to the actual workload pattern. 
Since io500/ior-hard does writes with a size of 47008 Bytes Quobyte can be adjusted to match this profile. 
This requires an adjusted object and segment size since they should be a multiple of each other. 
Also the chosen stripe size should be a multiple of the global count of MPI ranks (i.e. number nodes * number MPI ranks).

## Cross-Client consistent metadata

MDTest hard requires that metadata caching for non-existent files is turned off. 


