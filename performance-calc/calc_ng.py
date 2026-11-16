#!/usr/bin/env python3
"""Capacity and performance calculator for a storage cluster.

Standard library only. Usage:
    ./calc_ng.py -c myconfig.ini [-f text|json] [-s SECTION ...]

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
                    "devices_per_node", "device_write_mbs", "device_read_mbs",
                    "device_capacity_gb", "ec_data", "stripe_width", "replication_factor")
        for name in positive:
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be greater than 0")
        if self.controllers_per_node < 0 or self.controller_mbs < 0:
            raise ValueError("controller values must not be negative")
        if self.controllers_per_node > 0 and self.controller_mbs <= 0:
            raise ValueError("controller_mbs must be greater than 0 when controllers are used")
        if self.ec_coding < 0:
            raise ValueError("ec_coding must not be negative")

    # Derived values (all MB/s or GB)
    @property
    def has_controller(self) -> bool:
        """False for direct-attached devices (NVMe): no shared controller limit."""
        return self.controllers_per_node > 0

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
    cluster_nic = cfg.nodes * cfg.node_nic_mbs  # per direction

    limits = {
        "client_parallelism": n_clients * cfg.threads * stripes * device_mbs,
        "client_network": n_clients * cfg.client_nic_mbs / client_f,
        "backend_device": cluster_device / backend_f,
    }
    if cfg.has_controller:
        cluster_controller = cfg.nodes * cfg.controllers_per_node * cfg.controller_mbs
        limits["backend_controller"] = cluster_controller / backend_f
    if nic_in > 0:
        limits["storage_network_in"] = cluster_nic / nic_in
    if nic_out > 0:
        limits["storage_network_out"] = cluster_nic / nic_out
    return bottleneck(limits)


def build_results(cfg: Config) -> dict:
    node_device_w = cfg.devices_per_node * cfg.device_write_mbs
    node_device_r = cfg.devices_per_node * cfg.device_read_mbs
    node_controller = cfg.controllers_per_node * cfg.controller_mbs
    # None means there is no shared controller (direct-attached NVMe).

    results = {
        "client_count": cfg.clients,
        "client_threads": cfg.threads,
        "single_clientnode_network_throughput": format_rate(cfg.client_nic_mbs),
        "capacity_raw": format_capacity(cfg.raw_capacity_gb),
        "capacity_ec": format_capacity(usable_capacity_gb(cfg, "ec")),
        "capacity_repl": format_capacity(usable_capacity_gb(cfg, "repl")),
        "single_node_device_throughput_write": format_rate(node_device_w),
        "single_node_device_throughput_read": format_rate(node_device_r),
        "single_node_controller_throughput": (
            format_rate(node_controller) if cfg.has_controller else None),
        "single_node_network_throughput": format_rate(cfg.node_nic_mbs),
        "aggregated_device_throughput_write": format_rate(cfg.nodes * node_device_w),
        "aggregated_device_throughput_read": format_rate(cfg.nodes * node_device_r),
        "aggregated_controller_throughput": (
            format_rate(cfg.nodes * node_controller) if cfg.has_controller else None),
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

def md_table(headers: list, rows: list, align: str = "") -> str:
    """Render a Markdown table with padded columns, so it also reads well as
    plain text. align has one letter per column: l (left) or r (right).
    Default: first column left, the others right."""
    align = align or "l" + "r" * (len(headers) - 1)
    table = [[str(c) for c in headers]] + [[str(c) for c in row] for row in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(headers))]

    def fmt(row):
        cells = [cell.ljust(w) if a == "l" else cell.rjust(w)
                 for cell, w, a in zip(row, widths, align)]
        return "| " + " | ".join(cells) + " |"

    delimiter = "|" + "|".join(
        "-" * (w + 1) + ":" if a == "r" else "-" * (w + 2) for w, a in zip(widths, align)) + "|"
    return "\n".join([fmt(table[0]), delimiter] + [fmt(row) for row in table[1:]])


BAR_WIDTH = 20


def bar(fraction: float, width: int = BAR_WIDTH) -> str:
    """Text bar for a fraction between 0 and 1."""
    fraction = max(0.0, min(1.0, fraction))
    filled = round(fraction * width)
    if fraction > 0 and filled == 0:
        filled = 1
    return "\u2588" * filled + "\u2591" * (width - filled)


SHOW_CHOICES = ("all", "capacity", "ec", "replication", "performance")


def resolve_show(choices) -> tuple:
    """Translate --show choices into (capacity, hardware, protections).

    all          everything (default)
    capacity     capacity only
    ec           performance of erasure coding
    replication  performance of replication
    performance  performance of all three: EC, replication, no redundancy
    """
    if "all" in choices:
        return True, True, list(PROTECTIONS)
    selected = set()
    if "ec" in choices:
        selected.add("ec")
    if "replication" in choices:
        selected.add("repl")
    if "performance" in choices:
        selected.update(PROTECTIONS)
    return "capacity" in choices, False, [p for p in PROTECTIONS if p in selected]


def filter_results(results: dict, capacity: bool, hardware: bool, protections: list) -> dict:
    """Keep only the JSON keys that belong to the selected sections."""
    out = {}
    for key, value in results.items():
        if key.startswith("capacity_"):
            keep = capacity
        elif key.split("_")[0] in PROTECTIONS:
            keep = key.split("_")[0] in protections
        elif key in ("client_count", "client_threads"):
            keep = bool(protections) or hardware
        else:
            keep = hardware
        if keep:
            out[key] = value
    return out


def print_text(cfg: Config, r: dict, capacity: bool = True, hardware: bool = True,
               protections=PROTECTIONS) -> None:
    """Print the selected sections of the results as Markdown."""
    def rate(key):
        return rate_str(r[key]) if r[key] is not None else "n/a"

    blocks = ["# Cluster capacity and performance"]

    if hardware:
        devices = f"{cfg.devices_per_node} devices" + (
            "" if cfg.has_controller else " (no shared controller)")
        blocks.append("## Setup\n\n" + md_table(["Component", "Configuration"], [
            ["Storage", f"{cfg.nodes} nodes x {devices}, {cfg.node_nic_gbit:g} Gbit/s NIC per node"],
            ["Clients", f"{cfg.clients} clients x {cfg.threads} threads, "
                        f"{cfg.client_nic_gbit:g} Gbit/s NIC per client"],
            ["Protection", f"EC {cfg.ec_data}+{cfg.ec_coding}, {cfg.replication_factor}x "
                           f"replication, stripe width {cfg.stripe_width}"],
        ], align="ll"))

    if capacity:
        raw = cfg.raw_capacity_gb
        rows = []
        for label, key, gb in (("Raw", "capacity_raw", raw),
                               ("Erasure coding", "capacity_ec", usable_capacity_gb(cfg, "ec")),
                               ("Replication", "capacity_repl", usable_capacity_gb(cfg, "repl"))):
            share = gb / raw
            rows.append([label, r[key], f"{bar(share)} {share * 100:.1f}%"])
        blocks.append("## Capacity\n\n" + md_table(
            ["Type", "Capacity", "Share of raw"], rows, align="lrl"))

    if hardware:
        blocks.append("## Device performance\n\n" + md_table(["", "Write", "Read"], [
            ["Single node devices", rate("single_node_device_throughput_write"),
             rate("single_node_device_throughput_read")],
            ["Cluster devices", rate("aggregated_device_throughput_write"),
             rate("aggregated_device_throughput_read")],
            ["Single node controller", rate("single_node_controller_throughput"),
             rate("single_node_controller_throughput")],
            ["Cluster controller", rate("aggregated_controller_throughput"),
             rate("aggregated_controller_throughput")],
        ]))
        blocks.append("## Network performance\n\n" + md_table(["", "Storage nodes", "Clients"], [
            ["Single node", rate("single_node_network_throughput"),
             rate("single_clientnode_network_throughput")],
            ["Cluster", rate("aggregated_network_throughput"),
             rate("aggregated_client_network_throughput")],
        ]))

    if protections:
        # Bars are scaled to the highest throughput among the scenarios shown.
        values = {(p, m, o): evaluate(cfg, p, o, m == "multi")[0]
                  for p in protections for m in ("single", "multi") for o in ("write", "read")}
        top = max(values.values())
        for protection in protections:
            title = PROTECTION_TITLES[protection]
            blocks.append(f"## {title}")
            for mode in ("single", "multi"):
                rows = []
                for op in ("write", "read"):
                    prefix = f"{protection}_{mode}_{op}"
                    rows.append([op.capitalize(), rate(prefix + "_throughput"),
                                 bar(values[(protection, mode, op)] / top),
                                 f"`{r[prefix + '_bottleneck']}`"])
                blocks.append(f"### {mode.capitalize()} client, {title}\n\n" + md_table(
                    ["Operation", "Throughput", "Relative", "Bottleneck"], rows, align="lrll"))
        blocks.append(f"*Throughput with {cfg.threads} threads per client. Bars show the share "
                      "of the highest throughput shown.*")
    print("\n\n".join(blocks) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Calculate capacity and performance for a given hardware configuration.",
        epilog='Examples: ./calc_ng.py -c myconfig.ini   |   ./calc_ng.py -c myconfig.ini -s capacity   |   '
               './calc_ng.py -c myconfig.ini -s ec replication')
    parser.add_argument("-c", "--configfile", required=True, help="path to the INI config file")
    parser.add_argument("-f", "--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "-s", "--show", nargs="+", choices=SHOW_CHOICES, default=["all"], metavar="SECTION",
        help="what to show, one or more of: all (default), capacity, ec (performance of "
             "erasure coding), replication (performance of replication), performance "
             "(performance of all three: EC, replication, no redundancy)")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # the bars use block characters

    cfg = load_config(args.configfile)
    results = build_results(cfg)
    capacity, hardware, protections = resolve_show(args.show)
    if args.format == "json":
        print(json.dumps(filter_results(results, capacity, hardware, protections), indent=2))
    else:
        print_text(cfg, results, capacity, hardware, protections)


if __name__ == "__main__":
    main()
