#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from collections.abc import Mapping

from cmk.rulesets.v1 import Help, Label, Title
from cmk.rulesets.v1.form_specs import (
    BooleanChoice,
    CascadingSingleChoice,
    CascadingSingleChoiceElement,
    DefaultValue,
    DictElement,
    Dictionary,
    FixedValue,
    Integer,
    migrate_to_password,
    Password,
    String,
    validators,
)
from cmk.rulesets.v1.form_specs.validators import LengthInRange
from cmk.rulesets.v1.rule_specs import SpecialAgent, Topic


def _form_special_agent_proxmox_bs_special() -> Dictionary:
    return Dictionary(
        elements={
            "username": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("Username"),
                    help_text=Help("Full Username including login realm (e.g. @pam)"),
                    custom_validate=(validators.LengthInRange(min_value=1),),
                ),
            ),
            "password": DictElement(
                required=True,
                parameter_form=Password(
                    title=Title("Password"),
                    migrate=migrate_to_password,
                ),
            ),
            "port": DictElement(
                required=True,
                parameter_form=Integer(
                    title=Title("Port"),
                    prefill=DefaultValue(8007),
                    custom_validate=(validators.NetworkPort(),),
                ),
            ),
            # copied from cisco/cisco_prime
            "host": DictElement(
                required=True,
                parameter_form=CascadingSingleChoice(
                    elements=[
                        CascadingSingleChoiceElement(
                            name="ip_address",
                            title=Title("IP address"),
                            parameter_form=FixedValue(value=None),
                        ),
                        CascadingSingleChoiceElement(
                            name="host_name",
                            title=Title("Host name"),
                            parameter_form=FixedValue(value=None),
                        ),
                        CascadingSingleChoiceElement(
                            name="custom",
                            title=Title("Custom host"),
                            parameter_form=String(
                                title=Title("Custom host"),
                                label=Label("Host name or address"),
                                custom_validate=(LengthInRange(min_value=1),),
                                macro_support=True,
                            ),
                        ),
                    ],
                    prefill=DefaultValue("ip_address"),
                    title=Title("Specify PBS host via.."),
                ),
            ),
            "no_cert_check": DictElement(
                required=True,
                parameter_form=BooleanChoice(
                    title=Title("Disable SSL certificate validation"),
                    label=Label("SSL certificate validation is disabled"),
                ),
            ),
            "timeout": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("Query Timeout"),
                    help_text=Help("The network timeout in seconds"),
                    prefill=DefaultValue(50),
                    unit_symbol="seconds",
                    custom_validate=(validators.NumberInRange(min_value=1),),
                ),
            ),
            "cache_time": DictElement(
                required=False,
                parameter_form=Integer(
                    title=Title("Max Cache Age"),
                    help_text=Help("Time before the cache expires and new Data is read via API."),
                    prefill=DefaultValue(3600),
                    unit_symbol="seconds",
                    custom_validate=(validators.NumberInRange(min_value=30),),
                )
            ),
        },
        title=Title("Proxmox BS"),
    )


rule_spec_proxmox_bs = SpecialAgent(
    name="proxmox_bs",
    title=Title("Proxmox Backup Server"),
    topic=Topic.CLOUD,
    parameter_form=_form_special_agent_proxmox_bs_special,
    help_text=Help(
        "Proxmox Backup Server Monitoring (<tt>proxmox_bs</tt>)<br/>"
    ),
)
