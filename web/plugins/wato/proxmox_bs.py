#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Copyright (c) 2021 inett GmbH
#          Maximilian Hill <mhill@inett.de>
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file COPYING,
# which is part of this source code package.

from cmk.gui.i18n import _
from cmk.gui.plugins.wato import (
    HostRulespec,
    rulespec_registry,
)
from cmk.gui.cee.plugins.wato.agent_bakery.rulespecs.utils import (
    RulespecGroupMonitoringAgentsAgentPlugins
)
from cmk.gui.valuespec import (
    DropdownChoice,
)


def _valuespec_agent_config_proxmox_bs():
    return DropdownChoice(
        title = _("Proxmox Backup Server (Linux)"),
        help = _("This will deploy the agent plugin <tt>proxmox_bs</tt>"),
        choices = [
            ( 'server', _("Deploy plugin for Proxmox Backup Server") ),
            ( 'client', _("Deploy plugin for Proxmox Backup Client only")),
            ( None, _("Do not deploy plugin for Proxmox Backup") ),
        ]
    )


rulespec_registry.register(
    HostRulespec(
        group=RulespecGroupMonitoringAgentsAgentPlugins,
        name="agent_config:proxmox_bs",
        valuespec=_valuespec_agent_config_proxmox_bs,
    ))
