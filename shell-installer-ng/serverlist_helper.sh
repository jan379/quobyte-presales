gcloud compute instances list | awk '{print $5}' | grep ^[0-9] > gnodes.txt
