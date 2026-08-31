#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from cmk.rulesets.v1.form_specs import TimeMagnitude, SimpleLevels, LevelDirection
from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    DefaultValue,
    TimeSpan,
)
from cmk.rulesets.v1.rule_specs import Topic, CheckParameters, HostAndItemCondition


def _parameter_spec_proxmox_bs_sync_jobs() -> Dictionary:
    return Dictionary(
        title=Title("Proxmox Backup Server Sync Jobs"),
        help_text=Help("Configure the maximum age of the last successful Sync-Job."),
        elements={
            "age_levels": DictElement(
                required=True,
                parameter_form=SimpleLevels(
                    title=Title("PBS max sync job age"),
                    form_spec_template=TimeSpan(
                        displayed_magnitudes=[
                            TimeMagnitude.HOUR,
                            TimeMagnitude.DAY,
                        ],
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(
                        value=(
                            60.0 * 60.0 * 24.0 * 1.1,  # 1 Day
                            60.0 * 60.0 * 24.0 * 4.1   # 4 Days
                        )
                    )
                ),
            ),
        },
    )


rule_spec_proxmox_bs_sync_jobs = CheckParameters(
    title=Title("Proxmox Backup Server Sync Jobs"),
    topic=Topic.STORAGE,
    name="proxmox_bs_sync_jobs",
    parameter_form=_parameter_spec_proxmox_bs_sync_jobs,
    condition=HostAndItemCondition(
        item_title=Title("Sync-Job ID"),
    ),
    help_text=Help("Configure the maximum age of the last successful Sync-Job."),
)
