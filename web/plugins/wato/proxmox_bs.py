#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from cmk.gui.i18n import _
from cmk.gui.plugins.wato import (
    HostRulespec,
    rulespec_registry,
    CheckParameterRulespecWithItem,
    RulespecGroupCheckParametersStorage,
)
from cmk.gui.valuespec import (
    Alternative,
    Dictionary,
    FixedValue,
    Password,
    TextInput,
    Tuple,
    Age,
    Integer,
    TextAscii,
)


def _valuespec_agent_config_proxmox_bs():
    return Alternative(
        title = _("Proxmox Backup Server (Linux)"),
        help = _(
            "Proxmox Backup Server Monitoring (<tt>proxmox_bs</tt>)<br/>"
            "<b>This plugin may result in massive agent outputs</b>"
            ),
        style = 'dropdown',
        elements = [
            Dictionary(
                title = _("Deploy Proxmox Backup Server plugin"),
                elements = [
                    ( 'auth_user', TextInput(title=_("Username")) ),
                    ( 'auth_pass', Password(title=_("Password")) ),
                    ( 'fingerprint', TextInput(title=_("Fingerprint")) ),
                ],
                optional_keys = [],
            ),
            FixedValue(
                None,
                title = _("Do not deploy plugin for Proxmox Backup server"),
                totext = _("(disabled)"),
            )
        ],
    )


try:
    from cmk.gui.cee.plugins.wato.agent_bakery.rulespecs.utils import (
        RulespecGroupMonitoringAgentsAgentPlugins
    )

    rulespec_registry.register(
        HostRulespec(
            group=RulespecGroupMonitoringAgentsAgentPlugins,
            name="agent_config:proxmox_bs",
            valuespec=_valuespec_agent_config_proxmox_bs,
        ))
except ImportError:
    pass




def _parameter_proxmox_bs_clients():
    return Dictionary(
        required_keys=[],
        elements = [
            ('bkp_age',
                Tuple(
                    title = "Age of last backup before changing to warn or critical",
                    elements = [
                        Age(title=_("Warning at or above backup age"),
                            default_value = 604800, #warn after 7*24*60*60=604800 one week
                            help=_("If the backup is older than the specified time, the check changes to warn.")
                        ),
                        Age(title=_("Critical at or above backup age"),
                            default_value = 864000, #critical after 10*24*60*60=604800 10 days
                            help=_("If the backup is older than the specified time, the check changes to critical.")
                        ),
                    ]
                )
            ),
            ('snapshot_min_ok',
                Integer(title=_("Minium Snapshots with status OK"),
                    default_value = 1,
                    help=_("Change to warn, if not enough snapshots stored on the PBS Server")
                ),                
            )
        ]
    )

rulespec_registry.register(
    CheckParameterRulespecWithItem(
        check_group_name="proxmox_bs_clients",
        group=RulespecGroupCheckParametersStorage,
        item_spec=lambda: TextAscii(title=_('PBS Client ID'), ), #The text before the item Filter Box in a specific rule
        match_type='dict',
        parameter_valuespec=_parameter_proxmox_bs_clients,
        title=lambda: _("Proxmox Backup Server (PBS) Clients"),
    ))