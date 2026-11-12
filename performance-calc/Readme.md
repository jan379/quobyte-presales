# calc_ng.py

Estimates usable capacity and best-case throughput of a storage cluster from a
hardware description, and names the component that limits each scenario.
Python 3.8+, standard library only.

```
./calc_ng.py -c defaultconfig.ini            # text output
./calc_ng.py -c defaultconfig.ini -f json    # JSON output
```

`defaultconfig.ini` is a commented example: 6 storage nodes with 24 HDDs each,
100 Gbit/s server NICs, 200 Gbit/s client NICs, EC 5+3, 3x replication.

## Units

- Throughput is MB/s (decimal) internally. NIC speeds in the config are in
  Gbit/s and converted on load (1 Gbit/s = 125 MB/s).
- Capacity is GB (decimal).
- Output uses decimal units (MB/s, GB/s, TB/s, PB/s; GB, TB, PB).
- Rounding happens only when formatting output.

## Configuration

| Section | Key | Default | Meaning |
|---|---|---|---|
| `clients` | `number_clients` | 1 | Client machines |
| | `number_threads` | 1 | Parallel I/O threads per client |
| | `capacity_nic_gbs` | 1.0 | Client NIC, Gbit/s |
| `storagenodes` | `number_nodes` | 1 | Storage nodes |
| | `capacity_nic_gbs` | 1.0 | Storage node NIC, Gbit/s |
| | `number_devices` | 1 | HDDs per node |
| | `number_device_controller` | 1 | HDD controllers (HBAs) per node |
| | `device_throughput_mbs` | 100 | Sustained write per HDD, MB/s |
| | `device_throughput_mbs_read` | 100 | Sustained read per HDD, MB/s |
| | `controller_throughput_mbs` | 24000 | Throughput per controller, MB/s |
| | `capacity_devices_GB` | 100 | Capacity per HDD, GB |
| `storageconfig` | `ec_datastripes` | 5 | EC data stripes |
| | `ec_codingstripes` | 3 | EC coding stripes |
| | `replication_factor` | 3 | Number of copies |
| | `replication_stripewidth` | 1 | Devices a file is striped across (replication and unreplicated) |

Missing keys fall back to the defaults (a note is printed to stderr). Unknown
keys are reported as warnings, so a typo does not silently produce a plausible
but wrong result. Zero or negative values are rejected.

## Capacity

- Raw = nodes x devices per node x device capacity
- EC usable = raw x data / (data + coding)
- Replication usable = raw / replication_factor

## Throughput model

Every scenario is evaluated as the minimum of several named limits. The name
of the smallest one is reported as the bottleneck.

Scenarios: protection (EC, replication, no redundancy) x operation (read,
write) x clients (single client, or all clients in parallel).

### Limits

| Limit | Formula |
|---|---|
| `client_parallelism` | clients x threads x stripes x device throughput |
| `client_network` | clients x client NIC / client factor |
| `backend_device` | nodes x devices x device throughput / backend factor |
| `backend_controller` | nodes x controllers x controller throughput / backend factor |
| `storage_network_in` | nodes x node NIC / inbound factor |
| `storage_network_out` | nodes x node NIC / outbound factor |

"Clients" is 1 for single-client scenarios. "Stripes" is the EC data stripe
count for EC, and `replication_stripewidth` otherwise. Device throughput is
the read or write value, matching the operation.

### Traffic per byte of user data

NICs are full duplex, so inbound and outbound traffic on the storage nodes
are limited separately.

| Scenario | Client network | Storage NIC in | Storage NIC out | Devices and controllers |
|---|---|---|---|---|
| Replication, write | 1x | R x | (R - 1) x | R x |
| Replication, read | 1x | none | 1x | 1x |
| EC, write | (D+C)/D x | (D+C)/D x | none | (D+C)/D x |
| EC, read | 1x | none | 1x | 1x |
| No redundancy, write | 1x | 1x | none | 1x |
| No redundancy, read | 1x | none | 1x | 1x |

R = `replication_factor`, D = data stripes, C = coding stripes. With 5+3 the
EC write factor is 1.6, with R = 3 the replication write factors are 3 in and
2 out.

- **Replication is done by the storage system.** The client sends the data
  once to one server (the primary). The primary forwards it to the other
  R - 1 servers. All replicated traffic on the client network is therefore
  unreplicated.
- **Erasure coding is done by the client.** The client sends data and coding
  stripes directly to the servers, so on writes the frontend network carries
  the coding stripes as well (for 5+3: 5 data and 3 coding stripes per 5
  stripes of user data). On reads only the data stripes are fetched.

## Assumptions

- Data, and the primary role for replication, are spread evenly across all
  nodes and devices.
- Client traffic and replication traffic share the same storage NICs.
- Network speeds are line rate. Protocol overhead is not modeled.
- Acknowledgement and metadata traffic are ignored.
- The cluster is healthy. Degraded reads, rebuilds and recovery traffic are
  not modeled.
- Workloads are large sequential I/O. Small random I/O and IOPS are not
  modeled.
- The controller throughput value is used for both reads and writes. The
  expander backplane between controller and drives is not modeled.
- Capacity and throughput only: durability, failure domains and stripe
  placement are not evaluated.
- The results are best-case ceilings for the configured hardware, not
  predictions for a specific software stack.

## Choosing device throughput

Datasheet "sustained transfer rates" are peaks measured on the fast outer
tracks of a drive and overstate real averages. `defaultconfig.ini` therefore uses
conservative values: the lowest whole-disk averages among independently tested
data center drives, rounded down (217 MB/s write, 219 MB/s read), not the
285 MB/s peak on the Seagate Exos X24 data sheet. The Exos X24 itself was not
tested that way, so these values are estimates.

Sources:

- Seagate Exos X24 data sheet (DS2080):
  https://www.seagate.com/content/dam/seagate/nl_nl/content-fragments/products/datasheets/exos-x24/exos-x24-DS2080-2307US-nl_NL.pdf
- Independent whole-disk averages (HD Tune Pro) for the Exos X20, Exos M30 and
  Toshiba MG10/MG11:
  https://www.hardware-mag.de/artikel/festplatten_ssds/seagate_ironwolf_pro_32_tb_nas_hdd_im_test/8/
- Broadcom HBA 9500-16i product brief (13,700 MB/s sequential read):
  https://docs.broadcom.com/doc/BC-0510EN

## Output

Text output is Markdown. Capacity, device performance and network performance
are tables; each throughput scenario has its own sub-headline (for example
"Single client write, Replication") with its bottleneck and performance as two plain lines.
JSON output contains the same
data. Per-scenario keys follow the pattern
`<protection>_<single|multi>_<read|write>_bottleneck` and
`..._throughput`, with protection one of `ec`, `repl`, `unrepl`. Throughputs
are objects with `value` and `unit`.

Bottleneck names: `client_parallelism`, `client_network`, `backend_device`,
`backend_controller`, `storage_network_in`, `storage_network_out`.
