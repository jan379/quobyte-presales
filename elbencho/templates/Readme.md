# Collection of hopefully useful benchmark configurations

The usual syntax to start those benchmarks is

```
elbencho -c <myConfigFile> /path/to/a/quobyte/volume
```

To get a quick overview of a storage system you can

## 1) Measure local device performance

```
elbencho -c localdevice_throughput.elbencho 
```

## 2) Measure network throughput

```
elbencho -c netbench/netbench_allclients2allservers.elbencho 
```

## 3) Finally Measure Quobyte

```
elbencho -c parallel_throughput.elbencho /quobyte/elbencho
```

Expectation for a well balanced system is that you saturate your network, i.e. reach result from step 2) during step 3).
The system is balanced is all devices reach >90% utilization during writes.

Step 1) is to make sure that any vendor specs on device throughput can be matched.
