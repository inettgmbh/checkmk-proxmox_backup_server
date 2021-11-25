#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

import pprint
from pathlib import Path
from typing import Any, Dict

from .bakery_api.v1 import (
        FileGenerator,
        OS,
        Plugin,
        PluginConfig,
        register,
)


def get_proxmox_bs_files(conf: Dict[str, Any]) -> FileGenerator:
    if conf != None:
        yield Plugin(
            base_os=OS.LINUX,
            source=Path("proxmox_bs"),
            interval=3600,
      )
        yield PluginConfig(
            base_os=OS.LINUX,
            lines=[
                "export PBS_USERNAME=%s" % conf.get('auth_user'),
                "export PBS_PASSWORD=%s" % conf.get('auth_pass'),
            ],
            target=Path("proxmox_bs.env"),
        )


register.bakery_plugin(
    name="proxmox_bs",
    files_function=get_proxmox_bs_files,
)
