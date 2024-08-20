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
)


metric_group_count = Metric(
    name="group_count",
    title=Title("Number of backup groups"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_PURPLE,
)


metric_total_backups = Metric(
    name="total_backups",
    title=Title("Number of backups"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_PURPLE,
)


metric_verify_ok = Metric(
    name="verify_ok",
    title=Title("Snapshots successfully verified"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_PURPLE,
)


metric_verify_failed = Metric(
    name="verify_failed",
    title=Title("Snapshots with failed verification"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_ORANGE,
)


metric_verify_unknown = Metric(
    name="verify_unknown",
    title=Title("Snapshots with unknown verification status"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_ORANGE,
)


metric_verify_none = Metric(
    name="verify_none",
    title=Title("Unverified Snapshots"),
    unit=Unit(DecimalNotation("count")),
    color=Color.LIGHT_ORANGE,
)


graph_pbs_info = Graph(
    name="snapshots",
    title=Title("Backups"),
    minimal_range=MinimalRange("verify_ok:min", "total_backups:max"),
    compound_lines=[
        "verify_ok",
        "verify_failed",
        "verify_unknown",
        "verify_none",
    ],
    optional=[
        "verify_ok",
        "verify_failed",
        "verify_unknown",
        "verify_none",
    ],
)
