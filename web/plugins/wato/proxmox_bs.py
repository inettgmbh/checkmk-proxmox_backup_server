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
)
from cmk.gui.valuespec import (
    Alternative,
    Dictionary,
    FixedValue,
    Password,
    TextInput,
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
