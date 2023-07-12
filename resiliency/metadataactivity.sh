#!/usr/bin/env bash

# to be exectued on a client
for i in $(seq 64000); do 
	echo $i > file-$i && echo success $i; 
done
