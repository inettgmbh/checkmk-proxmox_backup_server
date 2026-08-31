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
    String,
    Password,
    Integer,
    DefaultValue, validators, migrate_to_password,
)
from cmk.rulesets.v1.rule_specs import AgentConfig, Topic


def _parameter_form_proxmox_bs_bakery() -> Dictionary:
    return Dictionary(
        title=Title("Proxmox Backup Server (Linux)"),
        help_text=Help("Deploy the local check agent"),
        elements={
            "auth": DictElement(
                required=False,
                parameter_form=Dictionary(
                    help_text=Help(
                    "Either username+password or authid+token can be used. "
                    "If disabled, a token will be created locally which is valid for a day."
                    ),
                    title=Title("Static Authentication"),
                    elements={
                        "authid": DictElement(
                            parameter_form=String(
                                title=Title("Username/AuthID"),
                            ),
                            required=True,
                        ),
                        "secret": DictElement(
                            parameter_form=Password(
                                title=Title("Password/Token"),
                                migrate=migrate_to_password,
                            ),
                            required=True,
                        ),
                    },
                ),
            ),
            "port": DictElement(
                parameter_form=Integer(
                    title=Title("Port"),
                    prefill=DefaultValue(8007),
                    custom_validate=(validators.NetworkPort(),),
                )
            ),
            "timeout": DictElement(
                parameter_form=Integer(
                    title=Title("Query Timeout"),
                    help_text=Help("The network timeout in seconds"),
                    prefill=DefaultValue(600),
                    unit_symbol="seconds",
                    custom_validate=(validators.NumberInRange(min_value=1),),
                )
            ),
            "agent_interval": DictElement(
                parameter_form=Integer(
                    title=Title("Agent Interval"),
                    help_text=Help("Execution Frequency in seconds. "
                                   "Default setting (3600) means that the cache will be renewed once per hour."),
                    prefill=DefaultValue(3600),
                    unit_symbol="seconds",
                    custom_validate=(validators.NumberInRange(min_value=30),),
                )
            )
        },
    )


rule_spec_proxmox_bs_local = AgentConfig(
    title=Title("Proxmox Backup Server"),
    topic=Topic.STORAGE,
    name="proxmox_bs_local",
    parameter_form=_parameter_form_proxmox_bs_bakery,
    help_text=Help(
        "Proxmox Backup Server Monitoring (<tt>proxmox_bs</tt>)<br/>"
    ),
)
