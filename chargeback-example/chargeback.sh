#!/usr/bin/env bash

# One of the Quobyte API endpoints to talsk to
API_ENDPOINT=http://api.quobyte-demo.com

# you should not use a shell script but something that supports floating point math!
CENT_BYTE=0.00003

# user login
qmgmt -u ${API_ENDPOINT} user login
# get a list of all tenant uuids
uuid_list=$(qmgmt -o json -u ${API_ENDPOINT} tenant list | jq -r '.[].tenant_id')

# get usage per tenant
for tenant in ${uuid_list}; do 
  tenant_usage=$(qmgmt -o json -u http://api.corp.quobyte.com usage show TENANT "${tenant}"  | jq .[0].LOGICAL_DISK_SPACE)
  echo "Tenant $tenant consumes ${tenant_usage} bytes."
  echo That is an equivalent of $(echo "${tenant_usage} * $CENT_BYTE" | bc -l ) cents.
done
