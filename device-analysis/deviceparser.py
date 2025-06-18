#!/usr/bin/env python3

import json
import pathlib
path = pathlib.Path('DEVICES.txt')

started = False
values = []
devices = []
hostnames = []
host_devices = []
tags = []
for line in path.read_text(encoding='utf-8').splitlines():
    if line.startswith('device {'):
        started = True
        continue
    if not started:
        continue
    # Skip registry devices
    if line.startswith('    content_type: DIR_DEVICE'):
        started = False 
        continue
    # Skip Metadata devices
    if line.startswith('    content_type: METADATA_DEVICE'):
        started = False 
        continue
    # Skip decommissioned devices
    if line.startswith('  status: DECOMMISSIONED'):
        started = False 
        continue
    if line.startswith('  device_id:'):
        dev_id = line.replace('  device_id: ', '')
    if line.startswith('    hostname: '):
        hostname = line.replace('    hostname: ', '')
    if line.startswith('    tags: '):
        newtag = line.replace('    tags: ', '')
        tags.append(newtag)
    if line.startswith('  detected_disk_type: '):
        hwtype = line.replace('  detected_disk_type: ', '')
    if line.startswith('    service_uuid:'):
        service_id = line.replace('    service_uuid: ', '')
    if line.startswith('    current_utilization:'):
        utilization = line.replace('    current_utilization: ', '')
    if line.startswith('    usedBytes:'):
        usage = line.replace('    usedBytes: ', '')
    if line.startswith('  device_capacity: '):
        capacity = line.replace('  device_capacity: ', '')
        devices.append( 
                {
                    "id": dev_id, 
                    "hostname": hostname, 
                    "capacity": capacity, 
                    "usage": usage,
                    "tags": tags,
                    "service_id": service_id,
                    "utilization": utilization,
                    "hwtype": hwtype
                    } 
                )
        tags = []

# get hostnames
for device in devices:
    if device["hostname"] not in hostnames:
        hostnames.append(device["hostname"])

for host in hostnames:
    thishost_devices = []
    for device in devices:
        if device["hostname"] == host:
            ##print("Device %s belongs to host %s" % (device["id"],host) )
            ##print("Device %s usage %s" % (device["id"], device["usage"]) )
            thishost_devices.append({"uuid": device["id"], "hwtype": device["hwtype"], "capacity": device["capacity"], "tags": device["tags"], "usage": device["usage"], "utilization": device["utilization"] })
    host_devices.append({"name": host, "devices": thishost_devices })

##print(host_devices[0])

def report(host_devices):
    for host in host_devices:
        print(host["name"])
        for device in host["devices"]:
            print("%s\t type: %s\t tags: %s\t capacity: %s TB\t usage: %s TB\t utilization: %s" % (device["uuid"], device["hwtype"], device["tags"], str(round(int(device["capacity"])/1024/1024/1024/1024, 2)), str(round(int(device["usage"])/1024/1024/1024/1024, 2)), str(round(float(device["utilization"]), 1))))
            ##print("%s\t type: %s\t tags: %s\t capacity: %s TB\t utilization: %s" % (device["uuid"], device["hwtype"], device["tags"], str(round(int(device["capacity"])/1024/1024/1024/1024, 2)), str(round(float(device["utilization"]), 1))))
        print("")

report(host_devices)

myjson = json.dumps(host_devices)
#print(myjson)
