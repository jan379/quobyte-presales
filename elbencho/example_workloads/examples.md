# Let's first bench the network, then the storage

# network benchmark. Needs elbencho deployed && started on all hosts that participate
## Clients send data
elbencho\
 --label arg="Bandwidth, clients send 1MB blocks and receive 1 bit."\
 --resfile /home/deploy/benchmarks/results/elbencho-$(date +%F).txt\
 --netbench\
 --servers quobyte-dataserver0,quobyte-dataserver1,quobyte-dataserver2\
 --clients quobyte-client0,quobyte-client1\
 --block 1m\
 --respsize 1\
 --threads 4\
 --size 100g\
 --timelimit 120\
 --lat

## Clients receive data
elbencho\
 --label arg="Bandwidth, clients send 1 bit blocks and receive 1 mega bit."\
 --resfile /home/deploy/benchmarks/results/elbencho-$(date +%F).txt\
 --netbench\
 --servers quobyte-dataserver0,quobyte-dataserver1,quobyte-dataserver2\
 --clients quobyte-client0,quobyte-client1\
 --block 1\
 --respsize 1m\
 --threads 4\
 --size 100g\
 --timelimit 120\
 --lat

## benchmark only nodes part of the cluster ("backend network test"), response-size and blocksize being the same 
elbencho\
 --label arg="Bandwidth, data services talk to each other bi-directional."\
 --resfile /home/deploy/benchmarks/results/elbencho-$(date +%F).txt\
 --netbench\
 --servers quobyte-dataserver0,quobyte-dataserver1,quobyte-dataserver2\
 --clients quobyte-coreserver0,quobyte-coreserver1,quobyte-coreserver2\
 --block 1m\
 --respsize 1m\
 --threads 4\
 --s 100g\
 --timelimit 120\
 --lat


# Write and read synchronous from any client listed in clients.list using 4 threads
elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list --write --read --delfiles --direct -b 1m --iodepth 1 -s 10g -t 4 /quobyte/elbencho/file{1..48}
# Write and read asynchronous from any client listed in clients.list using 4 threads
elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list --write --read --delfiles --direct -b 1m --iodepth 2 -s 10g -t 4 /quobyte/elbencho/file{1..48}


##elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list --write --read --direct -b 1m --iodepth 1 -s 10g -t 48 /quobyte/elbencho/file{1..48}
#elbencho --hostsfile /home/deploy/benchmarks/elbencho-clients.list -F -w -r -t 2 -d -n 100 -N 100 -s 1M -b 1M /quobyte/elbencho/

# Metadata workloads 

# create some volumes to work in parallel to distribute metadata workload/ saturate metadata services:
for i in $(seq 0 319); do qmgmt volume create r$i root root; done

# write with <N> clients using 32 threads in one directory (which is a dedicated volume then). 
# needs (#clients * 32) volumes to work; otherwise adjust number of threads, clients or volumes.

## Write and read small file data
elbencho --label arg="Small files, 4k"\
 --hostsfile /home/deploy/benchmarks/elbencho-clients.list\
 --resfile /home/deploy/benchmarks/results/elbencho-$(date +%F).txt\
 --write\
 --read\
 --threads 32\
 --mkdirs\
 --delfiles\
 --dirs 1\
 --files 6000\
 --size 4k\
 --block 4k /quobyte/

## Write files without content
elbencho --label arg="Zero byte files"\
 --hostsfile /home/deploy/benchmarks/elbencho-clients.list\
 --resfile /home/deploy/benchmarks/results/elbencho-$(date +%F).txt\
 --write\
 --read\
 --threads 32\
 --mkdirs\
 --delfiles\
 --dirs 1\
 --files 6000\
 --size 0\
 --block 4k /quobyte/

