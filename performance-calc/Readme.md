# Usage

```
jan@host.name% ./calc.py -c high_performance.ini 

# Welcome!

Your storage cluster consists of:
16	storage nodes
32	client nodes

## Capacity

| Redundancy                      	| GB      	| TB      	| PB       	|
| ------------------------------- 	| ------- 	| ------- 	| -------- 	|
| Capacity RAW	                  	| 652800   	| 652.8   	| 0.65    	|
| Capacity usable (EC 8+3)      	| 474763.64   	| 474.76   	| 0.47    	|
| Capacity usable (Replicated 3x)	| 217600.0   	| 217.6   	| 0.22    	|

## Performance

### Theoretical max. single client/ single stream performance data stored 3x replicated, stripe_width 16):
6720.0 MB/s
The upper limit is determined by device performance, including striping factor. Using faster devices or a broader stripe_width will increase performance.

### Theoretical max. multi client/ multi stream performance data stored 3x replicated, stripe_width 16, 32 clients):
53760.0 MB/s
The upper limit is determined by total storage device throughput, including replication penalty. Adding more storage devices will increase performance.

### Theoretical max. multi client/ multi stream performance data stored unreplicated, stripe_width 16, 32 clients):
161280.0 MB/s
The upper limit is determined by total storage device throughput. Adding more storage devices will increase performance.

### Theoretical max. single client/ single stream performance (data stored EC8+3):
3360.0 MB/s
The upper limit is determined by the performance of all data stripes written by a single client. Using faster devices or more data stripes will increase performance.

### Theoretical max. multi client/ multi stream performance (data stored EC8+3), 32 clients:
107520.0 MB/s
The upper limit is determined by the performance of all data stripes written by all clients. Using faster devices or more data stripes will increase performance.


```
