# Usage

```
[jan@jan performance-calc]$ ./calc.py -c high_performance.ini 

# Welcome!

Your storage cluster consists of:
16 storagenodes
16 clientnodes

## Capacity

### Capacity RAW:
652800 GB	 | 652.8 TB	 | 0.65 PB

### Capacity usable (EC 12+4):
489600.0 GB	 | 489.6 TB	 | 0.49 PB

### Capacity usable (Replicated 3x):
217600.0 GB	 | 217.6 TB	 | 0.22 PB


## Performance

### Theoretical max. single client/ single stream performance data stored 3x replicated, stripe_width 16):
6720.0 MB/s
The upper limit is determined by device performance, including striping factor. Using faster devices or a broader stripe_width will increase performance. (53760 mb/s)

### Theoretical max. multi client/ multi stream performance data stored 3x replicated, stripe_width 16, 32 clients):
53760.0 MB/s
The upper limit is determined by total storage device throughput, including replication penalty. Adding more storage devices will increase performance. (430080.0 mb/s)

### Theoretical max. multi client/ multi stream performance data stored unreplicated, stripe_width 16, 32 clients):
161280.0 MB/s
The upper limit is determined by total storage device throughput. Adding more storage devices will increase performance. (1290240 mb/s)

### Theoretical max. single client/ single stream performance (data stored EC12+4):
5040.0 MB/s
The upper limit is determined by the performance of all data stripes written by a single client. Using faster devices or more data stripes will increase performance. (40320 mb/s)

### Theoretical max. multi client/ multi stream performance (data stored EC12+4), 32 clients:
161280.0 MB/s
The upper limit is determined by the performance of all data stripes written by all clients. Using faster devices or more data stripes will increase performance. (1290240 mb/s)

```
