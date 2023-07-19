#!/usr/bin/env bash

# To be executed on a Quobyte volume mount
# stderr will go in a file
for i in $(seq 64000); do 
	echo $i > file-$i && echo success $i; 
done 2 > ioerrors-$(date +%F)
