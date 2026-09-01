#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from cmk.rulesets.v1 import Help, Title
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    MultilineText,
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    FixedValue,
    String, DefaultValue, BooleanChoice,
)
from cmk.rulesets.v1.rule_specs import Topic, DiscoveryParameters


def _parameter_form_proxmox_bs_snapshot_age_discovery() -> Dictionary:
    return Dictionary(
        title=Title("PBS Snapshot Age"),
        help_text=Help(
            "Monitors age of Backups in PBS Datastores."
        ),
        elements={
            "filter": DictElement(
                required=False,
                parameter_form=Dictionary(
                    title=Title("Monitor specific Datastores"),
                    help_text=Help("Use regex or a list of hosts to limit which Datastores will be monitored."),
                    elements={
                        "datastores": DictElement(
                            required=True,
                            parameter_form=CascadingSingleChoice(
                                title=Title("Host limit method"),
                                prefill=DefaultValue(value="all"),
                                elements=[
                                    CascadingSingleChoiceElement(
                                        title=Title("Monitor specified Datastores"),
                                        name="selected",
                                        parameter_form=MultilineText(
                                            title=Title("Monitored Datastores"),
                                            help_text=Help("Add one Datastore Name/Path per line. Case sensitive."),
                                        )
                                    ),
                                    CascadingSingleChoiceElement(
                                        title=Title("Monitor all Datastores"),
                                        name="all",
                                        parameter_form=FixedValue(
                                            value="all",
                                        )
                                    ),
                                    CascadingSingleChoiceElement(
                                        title=Title("Monitor Datastores by Regex"),
                                        name="regex",
                                        parameter_form=String(
                                            title=Title("Regex"),
                                            help_text=Help(
                                                "Monitored Datastores will be selected through this Regex. The Regex has to match against the Datastore name/path. Case sensitive."),
                                        )
                                    )
                                ]
                            )
                        ),
                        "limit_key": DictElement(
                            required=True,
                            parameter_form=CascadingSingleChoice(
                                title=Title("Host limit key"),
                                prefill=DefaultValue(value="name"),
                                elements=[
                                    CascadingSingleChoiceElement(
                                        title=Title("Filter by name"),
                                        name="name",
                                        parameter_form=FixedValue(
                                            value="name",
                                        ),
                                    ),
                                    CascadingSingleChoiceElement(
                                        title=Title("Filter by path"),
                                        name="path",
                                        parameter_form=FixedValue(
                                            value="path",
                                        )
                                    )
                                ]
                            )
                        )
                    }
                )
            ),
            "seperate_namespaces": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    title=Title("Separate Services for Namespaces"),
                    help_text=Help("Create separate Services for each Namespace. "
                                   "If disabled, a single summarized Service will be created."),
                    prefill=DefaultValue(False),
                )
            )
        }
    )


rule_spec_proxmox_bs_snapshot_age_discovery = DiscoveryParameters(
    title=Title("Proxmox Backup Server Snapshot Age"),
    topic=Topic.STORAGE,
    name="proxmox_bs_snapshot_age_discovery",
    parameter_form=_parameter_form_proxmox_bs_snapshot_age_discovery,
    help_text=Help("Used to limit the Datastores monitored.")
)
