#!/usr/bin/env bash

testvolumename="test"
primaryMDdevice=$(qmgmt volume show test -o json | jq -r .[0].primary_device_id)
primaryMDservice=$(qmgmt device show $primaryMDdevice -o json | jq .[0].host_name)

metadatapid=$(ps aux | grep metadata | awk '{print $2}')
sudo cpulimit -l 8 -m -p $metadatapid
