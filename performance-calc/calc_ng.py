#!/usr/bin/env python3
"""Capacity and performance calculator for a storage cluster.

Standard library only. Usage:
    ./calc_ng.py -c myconfig.ini [-f text|json]

Units (one convention, everywhere):
    * Throughput is MB/s (decimal megabytes per second) internally.
    * NIC speeds in the config are in Gbit/s and are converted to MB/s on load.
    * Device and controller throughput in the config are in MB/s.
    * Capacity is GB (decimal).
"""
from __future__ import annotations

import argparse
import configparser
import json
import sys
from dataclasses import dataclass

GBIT_TO_MBS = 1000 / 8  # 1 Gbit/s = 125 MB/s


# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

# (section, key, type, default, attribute name on Config)
SCHEMA = [
    ("clients", "number_clients", int, 1, "clients"),
    ("clients", "number_threads", int, 1, "threads"),
    ("clients", "capacity_nic_gbs", float, 1.0, "client_nic_gbit"),
    ("storagenodes", "number_nodes", int, 1, "nodes"),
    ("storagenodes", "capacity_nic_gbs", float, 1.0, "node_nic_gbit"),
    ("storagenodes", "number_devices", int, 1, "devices_per_node"),
    ("storagenodes", "number_device_controller", int, 1, "controllers_per_node"),
    ("storagenodes", "device_throughput_mbs", float, 100.0, "device_write_mbs"),
    ("storagenodes", "device_throughput_mbs_read", float, 100.0, "device_read_mbs"),
    ("storagenodes", "controller_throughput_mbs", float, 24000.0, "controller_mbs"),
    ("storagenodes", "capacity_devices_gb", float, 100.0, "device_capacity_gb"),
    ("storageconfig", "ec_datastripes", int, 5, "ec_data"),
    ("storageconfig", "ec_codingstripes", int, 3, "ec_coding"),
    ("storageconfig", "replication_stripewidth", int, 1, "stripe_width"),
    ("storageconfig", "replication_factor", int, 3, "replication_factor"),
]


@dataclass(frozen=True)
class Config:
    clients: int
    threads: int
    client_nic_gbit: float
    nodes: int
    node_nic_gbit: float
    devices_per_node: int
    controllers_per_node: int
    device_write_mbs: float
    device_read_mbs: float
    controller_mbs: float
    device_capacity_gb: float
    ec_data: int
    ec_coding: int
    stripe_width: int
    replication_factor: int

    def __post_init__(self):
        positive = ("clients", "threads", "client_nic_gbit", "nodes", "node_nic_gbit",
                    "devices_per_node", "controllers_per_node", "device_write_mbs",
                    "device_read_mbs", "controller_mbs", "device_capacity_gb",
                    "ec_data", "stripe_width", "replication_factor")
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than 0")
        if self.ec_coding < 0:
            raise ValueError("ec_coding must not be negative")

    # Derived values (all MB/s or GB)
    @property
    def client_nic_mbs(self) -> float:
        return self.client_nic_gbit * GBIT_TO_MBS

    @property
    def node_nic_mbs(self) -> float:
        return self.node_nic_gbit * GBIT_TO_MBS

    @property
    def raw_capacity_gb(self) -> float:
        return self.nodes * self.devices_per_node * self.device_capacity_gb


def load_config(path: str) -> Config:
    parser = configparser.ConfigParser()
    try:
        with open(path, "r") as f:
            parser.read_file(f)
    except OSError as e:
        sys.exit(f"Cannot open {path}: {e}")
    except configparser.Error as e:
        sys.exit(f"Could not parse {path}: {e}")

    # Typos silently falling back to defaults give plausible but wrong results.
    known = {(s, k) for s, k, *_ in SCHEMA}
    for section in parser.sections():
        for key in parser[section]:
            if (section, key) not in known:
                print(f"warning: unknown option [{section}] {key} (ignored)", file=sys.stderr)

    getters = {int: parser.getint, float: parser.getfloat, bool: parser.getboolean}
    values = {}
    for section, key, typ, default, attr in SCHEMA:
        if not parser.has_option(section, key):
            print(f"note: [{section}] {key} not set, using default {default}", file=sys.stderr)
        try:
            values[attr] = getters[typ](section, key, fallback=default)
        except ValueError as e:
            sys.exit(f"Invalid value for [{section}] {key}: {e}")
    try:
        return Config(**values)
    except ValueError as e:
        sys.exit(f"Invalid configuration: {e}")


# --------------------------------------------------------------------------
# Formatting (rounding happens only here)
# --------------------------------------------------------------------------

def format_capacity(gb: float) -> str:
    if gb >= 1000 * 1000:
        return f"{gb / 1000 / 1000:.2f} PB"
    if gb >= 1000:
        return f"{gb / 1000:.2f} TB"
    return f"{gb:.2f} GB"


def format_rate(mbs: float) -> dict:
    for unit, factor in (("PB/s", 1000 ** 3), ("TB/s", 1000 ** 2), ("GB/s", 1000)):
        if mbs >= factor:
            return {"value": round(mbs / factor, 2), "unit": unit}
    return {"value": round(mbs, 2), "unit": "MB/s"}


def rate_str(rate: dict) -> str:
    return f"{rate['value']} {rate['unit']}"


# --------------------------------------------------------------------------
# Model
# --------------------------------------------------------------------------

PROTECTIONS = ("ec", "repl", "unrepl")
PROTECTION_TITLES = {"ec": "Erasure Coding", "repl": "Replication", "unrepl": "No Redundancy"}


def bottleneck(limits: dict[str, float]) -> tuple[float, str]:
    """Return (throughput, name) of the most restrictive limit."""
    name = min(limits, key=limits.get)
    return limits[name], name


def usable_capacity_gb(cfg: Config, protection: str) -> float:
    if protection == "ec":
        return cfg.raw_capacity_gb * cfg.ec_data / (cfg.ec_data + cfg.ec_coding)
    if protection == "repl":
        return cfg.raw_capacity_gb / cfg.replication_factor
    return cfg.raw_capacity_gb


def evaluate(cfg: Config, protection: str, op: str, multi: bool) -> tuple[float, str]:
    """Throughput and bottleneck for one scenario.

    protection: 'ec' | 'repl' | 'unrepl';  op: 'read' | 'write';
    multi: all clients in parallel (True) or one client (False).

    Traffic model, per byte of user data (NICs are full duplex, so inbound
    and outbound traffic are limited separately; data is assumed to be spread
    evenly, so every node acts as primary/replica equally often):

      Replication (done by the storage system):
        write: the client sends the data once to one server (the primary), and
               the primary forwards it to the other (replication_factor - 1)
               servers.
               client network: 1x out
               storage NICs:   replication_factor x in (1 from the client,
                               replication_factor - 1 from the primary),
                               (replication_factor - 1) x out
               devices/controllers: replication_factor x
        read:  one copy is read. client 1x in, storage NICs 1x out, devices 1x.

      Erasure coding (done by the client):
        write: the client sends data AND coding stripes directly to the
               servers: (data+coding)/data x on the client network, on the
               storage NICs (in) and on devices/controllers.
        read:  only the data stripes are fetched (healthy cluster), 1x.

      No redundancy: 1x everywhere.
    """
    write = op == "write"
    n_clients = cfg.clients if multi else 1

    # (client network, storage NIC in, storage NIC out, devices/controllers)
    if protection == "ec":
        stripes = cfg.ec_data
        ec_factor = (cfg.ec_data + cfg.ec_coding) / cfg.ec_data
        if write:
            client_f, nic_in, nic_out, backend_f = ec_factor, ec_factor, 0.0, ec_factor
        else:
            client_f, nic_in, nic_out, backend_f = 1.0, 0.0, 1.0, 1.0
    else:
        stripes = cfg.stripe_width
        copies = cfg.replication_factor if protection == "repl" else 1
        if write:
            client_f, nic_in, nic_out, backend_f = 1.0, float(copies), float(copies - 1), float(copies)
        else:
            client_f, nic_in, nic_out, backend_f = 1.0, 0.0, 1.0, 1.0

    device_mbs = cfg.device_write_mbs if write else cfg.device_read_mbs
    cluster_device = cfg.nodes * cfg.devices_per_node * device_mbs
    cluster_controller = cfg.nodes * cfg.controllers_per_node * cfg.controller_mbs
    cluster_nic = cfg.nodes * cfg.node_nic_mbs  # per direction

    limits = {
        "client_parallelism": n_clients * cfg.threads * stripes * device_mbs,
        "client_network": n_clients * cfg.client_nic_mbs / client_f,
        "backend_device": cluster_device / backend_f,
        "backend_controller": cluster_controller / backend_f,
    }
    if nic_in > 0:
        limits["storage_network_in"] = cluster_nic / nic_in
    if nic_out > 0:
        limits["storage_network_out"] = cluster_nic / nic_out
    return bottleneck(limits)


def build_results(cfg: Config) -> dict:
    node_device_w = cfg.devices_per_node * cfg.device_write_mbs
    node_device_r = cfg.devices_per_node * cfg.device_read_mbs
    node_controller = cfg.controllers_per_node * cfg.controller_mbs

    results = {
        "client_count": cfg.clients,
        "client_threads": cfg.threads,
        "single_clientnode_network_throughput": format_rate(cfg.client_nic_mbs),
        "capacity_raw": format_capacity(cfg.raw_capacity_gb),
        "capacity_ec": format_capacity(usable_capacity_gb(cfg, "ec")),
        "capacity_repl": format_capacity(usable_capacity_gb(cfg, "repl")),
        "single_node_device_throughput_write": format_rate(node_device_w),
        "single_node_device_throughput_read": format_rate(node_device_r),
        "single_node_controller_throughput": format_rate(node_controller),
        "single_node_network_throughput": format_rate(cfg.node_nic_mbs),
        "aggregated_device_throughput_write": format_rate(cfg.nodes * node_device_w),
        "aggregated_device_throughput_read": format_rate(cfg.nodes * node_device_r),
        "aggregated_controller_throughput": format_rate(cfg.nodes * node_controller),
        "aggregated_network_throughput": format_rate(cfg.nodes * cfg.node_nic_mbs),
        "aggregated_client_network_throughput": format_rate(cfg.clients * cfg.client_nic_mbs),
    }
    for protection in PROTECTIONS:
        for mode, multi in (("single", False), ("multi", True)):
            for op in ("write", "read"):
                value, name = evaluate(cfg, protection, op, multi)
                prefix = f"{protection}_{mode}_{op}"
                results[f"{prefix}_bottleneck"] = name
                results[f"{prefix}_throughput"] = format_rate(value)
    return results


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def md_table(headers: list, rows: list) -> str:
    """Render a Markdown table with padded columns, so it also reads well as
    plain text. The first column is left-aligned, the others right-aligned."""
    table = [[str(c) for c in headers]] + [[str(c) for c in row] for row in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(headers))]

    def fmt(row):
        cells = [row[0].ljust(widths[0])]
        cells += [cell.rjust(w) for cell, w in zip(row[1:], widths[1:])]
        return "| " + " | ".join(cells) + " |"

    delimiter = "|" + "|".join(
        ["-" * (widths[0] + 2)] + ["-" * (w + 1) + ":" for w in widths[1:]]) + "|"
    return "\n".join([fmt(table[0]), delimiter] + [fmt(row) for row in table[1:]])


def print_text(cfg: Config, r: dict) -> None:
    """Print the results as Markdown."""
    def rate(key):
        return rate_str(r[key])

    print("# Cluster capacity and performance\n")

    print("## Capacity\n")
    print(md_table(["Type", "Capacity"], [
        ["Raw", r["capacity_raw"]],
        ["Erasure coding", r["capacity_ec"]],
        ["Replication", r["capacity_repl"]],
    ]))

    print("\n## Device performance\n")
    print(md_table(["", "Write", "Read"], [
        ["Single node devices", rate("single_node_device_throughput_write"),
         rate("single_node_device_throughput_read")],
        ["Cluster devices", rate("aggregated_device_throughput_write"),
         rate("aggregated_device_throughput_read")],
        ["Single node controller", rate("single_node_controller_throughput"),
         rate("single_node_controller_throughput")],
        ["Cluster controller", rate("aggregated_controller_throughput"),
         rate("aggregated_controller_throughput")],
    ]))

    print("\n## Network performance\n")
    print(md_table(["", "Storage nodes", "Clients"], [
        ["Single node", rate("single_node_network_throughput"),
         rate("single_clientnode_network_throughput")],
        ["Cluster", rate("aggregated_network_throughput"),
         rate("aggregated_client_network_throughput")],
    ]))

    for protection in PROTECTIONS:
        title = PROTECTION_TITLES[protection]
        print(f"\n## {title}")
        for mode in ("single", "multi"):
            for op in ("write", "read"):
                prefix = f"{protection}_{mode}_{op}"
                print(f"\n### {mode.capitalize()} client {op}, {title}\n")
                print(f"Bottleneck: `{r[prefix + '_bottleneck']}`\n")
                print(f"Performance, {cfg.threads} threads per client: "
                      f"{rate(prefix + '_throughput')}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate capacity and performance for a given hardware configuration.",
        epilog='Example: ./calc_ng.py -c myconfig.ini')
    parser.add_argument("-c", "--configfile", required=True, help="path to the INI config file")
    parser.add_argument("-f", "--format", choices=("text", "json"), default="text")
    args = parser.parse_args()

    cfg = load_config(args.configfile)
    results = build_results(cfg)
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        print_text(cfg, results)


if __name__ == "__main__":
    main()
