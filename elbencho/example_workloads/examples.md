
Basic Options:
  -d [ --mkdirs ]       Create directories. (Already existing dirs are not treated as error.)
  -w [ --write ]        Write files. Create them if they don't exist.
  -r [ --read ]         Read files.
  --stat                Read file status attributes (file size, owner etc).
  -F [ --delfiles ]     Delete files.
  -D [ --deldirs ]      Delete directories.
  -t [ --threads ] arg  Number of I/O worker threads. (Default: 1)
  -n [ --dirs ] arg     Number of directories per I/O worker thread. This can be 0 to disable creation of any subdirs, in which case all workers share the given dir. (Default: 1)
  -N [ --files ] arg    Number of files per thread per directory. (Default: 1) Example: "-t2 -n3 -N4" will use 2x3x4=24 files.
  -s [ --size ] arg     File size. (Default: 0)
  -b [ --block ] arg    Number of bytes to read/write in a single operation. (Default: 1M)

Frequently Used Options:
  --direct              Use direct IO.
  --iodepth arg         Depth of I/O queue per thread for asynchronous read/write. Setting this to 2 or higher turns on async I/O. (Default: 1)
  --lat                 Show minimum, average and maximum latency for read/write operations and entries. In read and write phases, entry latency includes file open, read/write and close.


The number of clients depends on the elbencho-clients.list, of course

# Write and read synchronous from any client listed in clients.list using 4 threads
elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list --write --read --delfiles --direct -b 1m --iodepth 1 -s 10g -t 4 /quobyte/elbencho/file{1..48}
# Write and read asynchronous from any client listed in clients.list using 4 threads
elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list --write --read --delfiles --direct -b 1m --iodepth 2 -s 10g -t 4 /quobyte/elbencho/file{1..48}


# network benchmark. Needs elbencho deployed && started on all hosts taht participate
## Clients send data
elbencho --netbench --servers quobyte-dataserver0,quobyte-dataserver1,quobyte-dataserver2 --clients quobyte-client0,quobyte-client1 -b 1m --respsize 1  -t 4 -s 100g --timelimit 10

## Clients receive data(?)
elbencho --netbench --servers quobyte-dataserver0,quobyte-dataserver1,quobyte-dataserver2 --clients quobyte-client0,quobyte-client1 -b 1 --respsize 1m  -t 4 -s 100g --timelimit 10

## benchmark only nodes part of the cluster ("backend network test"), response-size and blocksize being the same 
elbencho --netbench --servers quobyte-dataserver0,quobyte-dataserver1,quobyte-dataserver2 --clients quobyte-coreserver0,quobyte-coreserver1,quobyte-coreserver2 -b 1m --respsize 1m  -t 4 -s 100g --timelimit 30 --lat

##elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list --write --read --direct -b 1m --iodepth 1 -s 10g -t 48 /quobyte/elbencho/file{1..48}
#elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list -F -w -r -t 2 -d -n 100 -N 100 -s 1M -b 1M /quobyte/elbencho/

# Metadata workloads 

# create some volumes to work in parallel to distribute metadata workload/ saturate metadata services:
for i in $(seq 0 319); do qmgmt volume create r$i root root; done

# write with <N> clients using 32 threads in one directory (which is a dedicated volume then). 
# needs (#clients * 32) volumes to work; otherwise adjust number of threads, clients or volumes.

## write real data
elbencho --label arg="Small files, 4k"\
 --hostsfile /home/deploy/benchmarks/elbencho-clients.list\
 --resfile /home/deploy/benchmarks/results/elbencho-$(date +%F).txt
 --write\
 --read\
 --threads 32\
 --mkdirs\
 --delfiles\
 --dirs 1 --files 6000\
 --size 4k\
 --block 4k /quobyte/


## write only metadata data
elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list -w -r -t 32 -d -F -n 1 -N 6000 -s 0k -b 0k /quobyte/
