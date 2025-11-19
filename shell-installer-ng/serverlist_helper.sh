gcloud compute instances list | awk '{print $6}' | grep ^[0-9] > gnodes.txt
