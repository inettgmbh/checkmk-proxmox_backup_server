#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from cmk.graphing.v1 import Title
from cmk.graphing.v1.graphs import Graph, MinimalRange
from cmk.graphing.v1.metrics import (
    Metric,
    Unit,
    DecimalNotation,
    Color,
    StrictPrecision,
)


metric_proxmox_bs_group_count = Metric(
    name="proxmox_bs_group_count",
    title=Title("Number of backup groups"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_PURPLE,
)


metric_proxmox_bs_backup_count = Metric(
    name="proxmox_bs_backup_count",
    title=Title("Number of backups"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_PURPLE,
)


metric_proxmox_bs_verify_ok = Metric(
    name="proxmox_bs_verify_ok",
    title=Title("Snapshots successfully verified"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_PURPLE,
)


metric_proxmox_bs_verify_fail = Metric(
    name="proxmox_bs_verify_fail",
    title=Title("Snapshots with failed verification"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_ORANGE,
)


metric_proxmox_bs_verify_unknown = Metric(
    name="proxmox_bs_verify_unknown",
    title=Title("Snapshots with unknown verification status"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_ORANGE,
)


metric_proxmox_bs_verify_none = Metric(
    name="proxmox_bs_verify_none",
    title=Title("Unverified Snapshots"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_ORANGE,
)


graph_proxmox_bs_info = Graph(
    name="snapshots",
    title=Title("Backups"),
    minimal_range=MinimalRange("verify_ok:min", "total_backups:max"),
    compound_lines=[
        "proxmox_bs_verify_ok",
        "proxmox_bs_verify_fail",
        "proxmox_bs_verify_unknown",
        "proxmox_bs_verify_none",
    ],
    optional=[
        "proxmox_bs_verify_ok",
        "proxmox_bs_verify_fail",
        "proxmox_bs_verify_unknown",
        "proxmox_bs_verify_none",
    ],
)


metric_proxmox_bs_sync_job_success_percentage = Metric(
    name="proxmox_bs_sync_job_success_percentage",
    title=Title("% of recent successful Synchronization Jobs"),
    unit=Unit(DecimalNotation("%"), StrictPrecision(digits=2)),
    color=Color.CYAN,
)
