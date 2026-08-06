 kubectl get pods -l app=elbencho -o jsonpath='{range .items[*]}{.status.podIP}{"\n"}{end}' > /tmp/elbencho-hosts.txt
 COORDINATOR_POD=$(kubectl get pods -l app=elbencho -o jsonpath='{.items[0].metadata.name}')
 kubectl cp /tmp/elbencho-hosts.txt $COORDINATOR_POD:/tmp/hosts.txt
 kubectl exec -it $COORDINATOR_POD -- elbencho --hostsfile /tmp/hosts.txt --threads 8 --size 1g --block 1m --write --direct --files 1 --dirs 0 /mnt/quobyte-volume
