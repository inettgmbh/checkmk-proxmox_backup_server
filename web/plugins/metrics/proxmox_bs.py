#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from cmk.gui.i18n import _
from cmk.gui.plugins.metrics import (
    check_metrics,
    metric_info,
    graph_info,
    MB,
)

metric_info['group_count'] = {
    'title': _('Number of backup groups'),
    'unit' : 'count',
    'color': indexed_color(1, 6),
}

metric_info['total_backups'] = {
    'title': _('Number of backups'),
    'unit' : 'count',
    'color': indexed_color(2, 6),
}
metric_info['verify_ok'] = {
    'title': _('Snapshots successfully verified'),
    'unit' : 'count',
    'color': indexed_color(3, 6),
}
metric_info['verify_failed'] = {
    'title': _('Snapshots with failed verification'),
    'unit' : 'count',
    'color': indexed_color(4, 6),
}
metric_info['verify_unknown'] = {
    'title': _('Snapshots with unknown verification status'),
    'unit' : 'count',
    'color': indexed_color(5, 6),
}
metric_info['verify_none'] = {
    'title': _('Snapshots yet to be verified'),
    'unit' : 'count',
    'color': indexed_color(6, 6),
}

graph_info['snapshots'] = {
    'title': _('Backups'),
    'metrics': [
        ('verify_ok', 'stack', metric_info['verify_ok']['title']),
        ('verify_failed', 'stack', metric_info['verify_failed']['title']),
        ('verify_unknown', 'stack', metric_info['verify_unknown']['title']),
        ('verify_none', 'stack', metric_info['verify_none']['title']),
    ],
    'optional_metrics': [
        'verify_ok',
        'verify_failed',
        'verify_unknown',
        'verify_none',
    ],
    'range': ('verify_ok:min', 'total_bakups:max'),
}

