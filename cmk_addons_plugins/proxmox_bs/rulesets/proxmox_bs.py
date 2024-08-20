#!/usr/bin/env python3

from cmk.rulesets.v1 import Help, Title, Label
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    String,
    Password,
)
from cmk.rulesets.v1.rule_specs import Topic, AgentConfig


def _parameter_form_proxmox_bs() -> Dictionary:
    return Dictionary(
        title=Title("Proxmox Backup Server (Linux)"),
        help_text=Help(
            "Required Host Specific Parameters."
        ),
        elements={
            'auth_user': DictElement(
                parameter_form=String(
                    title=Title("Username")
                ),
                required=True,
            ),
            'auth_pass': DictElement(
                parameter_form=Password(
                    title=Title("Password")
                ),
                required=True,
            ),
            'dns_name': DictElement(
                parameter_form=String(
                    title=Title("PBS host DNS name with Port, if not default")
                ),
                required=True,
            ),
            'fingerprint': DictElement(
                parameter_form=String(
                    title=Title("Fingerprint")
                ),
                required=True,
            ),
        }
    )


rule_spec_pbs_snapshot_age = AgentConfig(
    title=Title("Proxmox Backup Server (Linux)"),
    topic=Topic.STORAGE,
    name="proxmox_bs",
    parameter_form=_parameter_form_proxmox_bs,
    help_text=Help(
        "Proxmox Backup Server Monitoring (<tt>proxmox_bs</tt>)<br/>"
        "<b>This plugin may result in massive agent outputs</b>"
    )
)
