# create some volumes to work in parallel:

# generate 320 volumes; assuming 10 clients
for i in $(seq 160 319); do qmgmt volume create r$i root root; done

# write with <N> clients using 32 threads in one directory (which is a dedicated volume then). 
# needs (#clients * 32) volumes to work; otherwise adjust number of threads, clients or volumes.

## write real data
elbencho --hostsfile /home/deploy/elbencho-clients.list -w -r -t 32 -d  -F -n 1 -N 6000 -s 4k -b 4k /quobyte/
## write only metadata data
elbencho --hostsfile /home/deploy/elbencho-clients.list -w -r -t 32 -d  -F -n 1 -N 6000 -s 0k -b 0k /quobyte/
