# calc_ng.py

Estimates usable capacity and best-case throughput of a storage cluster from a
hardware description, and names the component that limits each scenario.
Python 3.8+, standard library only.

```
./calc_ng.py -c default.ini            # text output
./calc_ng.py -c default.ini -f json    # JSON output
./calc_ng.py -c default.ini -s capacity
./calc_ng.py -c default.ini -s ec replication
```

`-s` / `--show` selects what is shown, in text and in JSON output. It takes one
or more of:

| Value | Shows |
|---|---|
| `all` (default) | everything: capacity, device and network performance, and all scenarios |
| `capacity` | capacity only |
| `ec` | performance of erasure coding |
| `replication` | performance of replication |
| `performance` | performance of all three: EC, replication and no redundancy |

The device and network performance tables are part of the full output (`all`)
only.

Two commented example configs are included, both with 6 storage nodes, EC 5+3
and 3x replication:

- `default.ini`: 24 HDDs per node behind an HBA, 100 Gbit/s server NICs,
  4 clients with 200 Gbit/s NICs.
- `nvme.ini`: all-flash with 8 directly attached NVMe SSDs per node, sized so
  devices and network are balanced (400 Gbit/s server NICs, 12 clients with
  200 Gbit/s NICs).

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
| | `number_devices` | 1 | Devices (HDDs or SSDs) per node |
| | `number_device_controller` | 1 | HDD controllers (HBAs) per node. 0 = no shared controller (NVMe), see below |
| | `device_throughput_mbs` | 100 | Sustained write per device (HDD or SSD), MB/s |
| | `device_throughput_mbs_read` | 100 | Sustained read per device, MB/s |
| | `controller_throughput_mbs` | 24000 | Throughput per controller, MB/s (ignored if there is no controller) |
| | `capacity_devices_GB` | 100 | Capacity per device, GB |
| `storageconfig` | `ec_datastripes` | 5 | EC data stripes |
| | `ec_codingstripes` | 3 | EC coding stripes |
| | `replication_factor` | 3 | Number of copies |
| | `replication_stripewidth` | 1 | Devices a file is striped across (replication and unreplicated) |

**All-flash / NVMe:** NVMe SSDs attach directly via PCIe, so there is no shared
HDD controller. Set `number_device_controller = 0` (and
`controller_throughput_mbs = 0`) and the `backend_controller` limit is left out
of the calculation. The controller rows in the text output show `n/a` and the
controller values in the JSON output are `null`.

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
| `backend_controller` | nodes x controllers x controller throughput / backend factor (only if controllers > 0) |
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
- For directly attached NVMe, PCIe lanes, root complexes and CPU/memory
  bandwidth are not modeled.
- Capacity and throughput only: durability, failure domains and stripe
  placement are not evaluated.
- The results are best-case ceilings for the configured hardware, not
  predictions for a specific software stack.

## Choosing device throughput

Datasheet "sustained transfer rates" are peaks measured on the fast outer
tracks of a drive and overstate real averages. `default.ini` therefore uses
conservative values: the lowest whole-disk averages among independently tested
data center drives, rounded down (217 MB/s write, 219 MB/s read), not the
285 MB/s peak on the Seagate Exos X24 data sheet. The Exos X24 itself was not
tested that way, so these values are estimates.

For NVMe SSDs (`nvme.ini`) the data sheet sequential figures are used as they
are (Micron 7450 PRO 7.68TB: 6800 MB/s read, 5600 MB/s write). They are not
outer-track peaks like HDD figures, and an independent steady-state test
measured sequential writes of about 5750 MB/s and reads of about 7000 MB/s,
at or above the data sheet.

Sources:

- Seagate Exos X24 data sheet (DS2080):
  https://www.seagate.com/content/dam/seagate/nl_nl/content-fragments/products/datasheets/exos-x24/exos-x24-DS2080-2307US-nl_NL.pdf
- Independent whole-disk averages (HD Tune Pro) for the Exos X20, Exos M30 and
  Toshiba MG10/MG11:
  https://www.hardware-mag.de/artikel/festplatten_ssds/seagate_ironwolf_pro_32_tb_nas_hdd_im_test/8/
- Broadcom HBA 9500-16i product brief (13,700 MB/s sequential read):
  https://docs.broadcom.com/doc/BC-0510EN
- Micron 7450 SSD product page:
  https://www.microncpg.com/products/ssd/micron-7450-ssd
- Independent steady-state test of the Micron 7450 PRO 7.68TB:
  https://www.tweaktown.com/reviews/10278/micron-7450-pro-7-68tb-enterprise-ssd-double-density/index.html

## Output

Text output is Markdown, padded so it also reads well unrendered:

- **Setup**: a short summary of the configured storage, clients and protection.
- **Capacity**: a table with a bar showing each usable capacity as a share of
  raw.
- **Device performance** and **Network performance**: tables.
- **Erasure Coding**, **Replication**, **No Redundancy**: per protection a
  sub-headline for single client and multi client, each with a table of write
  and read throughput, a bar relative to the highest throughput shown, and the
  bottleneck.

The bars use block characters, so the output is written as UTF-8. With `-s`
only the selected sections are printed.

JSON output contains the same
data. Per-scenario keys follow the pattern
`<protection>_<single|multi>_<read|write>_bottleneck` and
`..._throughput`, with protection one of `ec`, `repl`, `unrepl`. Throughputs
are objects with `value` and `unit`. Controller throughputs are `null` when
there is no controller.

Bottleneck names: `client_parallelism`, `client_network`, `backend_device`,
`backend_controller`, `storage_network_in`, `storage_network_out`.
