#!/usr/bin/env bash

metadatapid=$(ps aux | grep metadata | awk '{print $2}')
sudo cpulimit -l 8 -m -p $metadatapid
