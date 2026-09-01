#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from cmk.rulesets.v1 import Help, Title, Label
from cmk.rulesets.v1.form_specs import (
    DefaultValue,
    DictElement,
    Dictionary,
    LevelDirection,
    SimpleLevels,
    TimeMagnitude,
    TimeSpan,
    BooleanChoice,
)
from cmk.rulesets.v1.rule_specs import (
    Topic,
    CheckParameters,
    HostAndItemCondition,
)


def _parameter_form_proxmox_bs_snapshot_age() -> Dictionary:
    return Dictionary(
        title=Title("PBS Snapshot Age"),
        help_text=Help(
            "Parameters to set thresholds for Snapshot Age, as well as if the Service should return WRN/CRT."
        ),
        elements={
            "throw_warnings": DictElement(
                parameter_form=BooleanChoice(label=Label("Throw Errors on Match")),
                required=True,
            ),
            "age_levels": DictElement(
                parameter_form=SimpleLevels(
                    title=Title("Wrn/Crt Day Threshold"),
                    help_text=Help(
                        "If Snapshot Age is greater than this, it will yield a WRN"
                    ),
                    form_spec_template=TimeSpan(
                        displayed_magnitudes=[TimeMagnitude.DAY, TimeMagnitude.HOUR],
                    ),
                    level_direction=LevelDirection.UPPER,
                    prefill_fixed_levels=DefaultValue(
                        value=(
                            2.0 * 24.0 * 60.0 * 60.0 + 60.0 * 60.0 * 2.0,
                            10.0 * 24.0 * 60.0 * 60.0 + 60.0 * 60.0 * 2.0,
                        )
                    ),
                ),
                required=True,
            ),
            "ignore_old_errors": DictElement(
                required=False,
                parameter_form=TimeSpan(
                    title=Title("Ignore Backup if no Snapshot has been made in X days"),
                    help_text=Help(
                        "If the oldest Snapshot of  Backup Group is X days or older, it will not throw warnings."
                    ),
                    displayed_magnitudes=[TimeMagnitude.DAY, TimeMagnitude.HOUR],
                    prefill=DefaultValue(value=365.0 * 24.0 * 60.0 * 60.0 + 60.0 * 60.0 * 2.0),
                ),
            ),
        },
    )


rule_spec_proxmox_bs_snapshot_age = CheckParameters(
    title=Title("Proxmox Backup Server Snapshot Age"),
    topic=Topic.STORAGE,
    name="proxmox_bs_snapshot_age",
    parameter_form=_parameter_form_proxmox_bs_snapshot_age,
    help_text=Help("Adjust monitoring rules for <tt>proxmox_bs_snapshot_age</tt>."),
    condition=HostAndItemCondition(
        item_title=Title("Datastore Path"),
    ),
)
