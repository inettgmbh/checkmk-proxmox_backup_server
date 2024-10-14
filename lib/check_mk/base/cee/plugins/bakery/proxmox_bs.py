#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

import pprint
import sys
from pathlib import Path
from typing import Any, Dict

from .bakery_api.v1 import (
        FileGenerator,
        OS,
        Plugin,
        PluginConfig,
        register,
)

from cmk.utils import password_store


def get_proxmox_bs_files(conf: Dict[str, Any]) -> FileGenerator:
    if conf is not None:
        yield Plugin(
            base_os=OS.LINUX,
            source=Path("proxmox_bs"),
            interval=3600,
        )
        password = conf.get('auth_pass')
        if password[1] == "explicit_password":
            secret = password[2][1]
        elif password[1] == "stored_password":
            secret = password_store.lookup(password_store.password_store_path(), password[2][0])
        else:
            secret = ""
            sys.exit(1)
        yield PluginConfig(
            base_os=OS.LINUX,
            lines=[
                f"export PBS_USERNAME='{conf.get('auth_user')}'",
                f"export PBS_PASSWORD='{secret}'",
                f"export PBS_DNS_NAME='{conf.get('dns_name')}'",
                f"export PBS_FINGERPRINT='{conf.get('fingerprint')}'",
            ],
            target=Path("proxmox_bs.env"),
        )


register.bakery_plugin(
    name="proxmox_bs",
    files_function=get_proxmox_bs_files,
)
