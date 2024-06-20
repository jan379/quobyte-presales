
The number of clients depends on the elbencho-clients.list, of course

# Write and read synchronous from any client listed in clients.list using 4 threads
elbencho --hostsfile /home/deploy/elbencho-clients.list --write --read --direct -b 1m --iodepth 1 -s 10g -t 4 /quobyte/elbencho/file{1..48}
# Write and read asynchronous from any client listed in clients.list using 4 threads
elbencho --hostsfile /home/deploy/elbencho-clients.list --write --read --direct -b 1m --iodepth 2 -s 10g -t 4 /quobyte/elbencho/file{1..48}




##elbencho --hostsfile /home/deploy/elbencho-clients.list --write --read --direct -b 1m --iodepth 1 -s 10g -t 48 /quobyte/elbencho/file{1..48}
#elbencho --hostsfile /home/deploy/elbencho-clients.list -F -w -r -t 2 -d -n 100 -N 100 -s 1M -b 1M /quobyte/elbencho/
