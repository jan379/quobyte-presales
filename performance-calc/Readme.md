# Usage

```
[jan@jan performance-calc]$ ./calc.py -c high_density.ini 

# Welcome!

Your storage cluster consists of:
4 storagenodes
4 clientnodes

## Capacity

### Capacity RAW:
7744000 GB	 | 7562.5 TB	 | 7.39 PB

### Capacity usable (EC 5+3):
4840000.0 GB	 | 4726.56 TB	 | 4.62 PB

### Capacity usable (Replicated 3x):
2581333.33 GB	 | 2520.83 TB	 | 2.46 PB


## Performance

### Theoretical max. single client/ single stream performance data stored 3x replicated, stripe_width 1):
80.0 MB/s
The upper limit is determined by device performance, including striping factor. Using faster devices or a broader stripe_width will increase performance. (640 mb/s)

### Theoretical max. multi client/ multi stream performance data stored 3x replicated, stripe_width 1, 2 clients):
160.0 MB/s
The upper limit is determined by device throughput of devices clients write to, including striping. Using more clients or more stripes will increase performance. (1280 mb/s)

### Theoretical max. multi client/ multi stream performance data stored unreplicated, stripe_width 1, 2 clients):
160.0 MB/s
The upper limit is determined by device throughput of devices clients write to, including striping. Using more clients or broader stripe_width will increase performance (1280 mb/s)

### Theoretical max. single client/ single stream performance (data stored EC5+3):
400.0 MB/s
The upper limit is determined by the performance of all data stripes written by a single client. Using faster devices or more data stripes will increase performance. (3200 mb/s)

### Theoretical max. multi client/ multi stream performance (data stored EC5+3), 2 clients:
800.0 MB/s
The upper limit is determined by the performance of all data stripes written by all clients. Using faster devices or more data stripes will increase performance. (6400 mb/s)

(failed reverse-i-search)`dd if': git commit -m"a^C ec multi client" calc.py 
(failed reverse-i-search)`if= ': git d^Cf high_performance.ini
[jan@jan performance-calc]$ dd if=/dev/zero of=testfile bs=8m count=10
dd: invalid number: ‘8m’
[jan@jan performance-calc]$ dd if=/dev/zero of=testfile bs=8M count=10
10+0 records in
10+0 records out
83886080 bytes (84 MB, 80 MiB) copied, 0.063862 s, 1.3 GB/s
```


