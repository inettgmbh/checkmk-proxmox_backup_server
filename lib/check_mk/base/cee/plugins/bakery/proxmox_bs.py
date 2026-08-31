#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

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


def get_proxmox_bs_local_files(conf: Dict[str, Any]) -> FileGenerator:
    if conf is not None:
        yield Plugin(
            base_os=OS.LINUX,
            source=Path("proxmox_bs"),
            interval=conf.get('agent_interval', 3600),
        )
        if conf.get('auth', None) is not None:
            password = conf['auth']['secret']
            authid = conf['auth']['authid']
            if password[1] == "explicit_password":
                secret = password[2][1]
            elif password[1] == "stored_password":
                secret = password_store.lookup(
                    password_store.password_store_path(), password[2][0]
                )
            else:
                secret = ""

            lines = [
                "[auth]",
                "auth_option = simple",
                f"authid = {authid}",
                f"token = {secret}",
                "[connection]",
            ]

        else:
            lines = [
                "[auth]",
                "auth_option = auto",
                "[connection]",
            ]

        lines.append(f"port = {conf.get("port", 8007)}")
        lines.append(f"timeout = {conf.get('timeout', 600)}")

        yield PluginConfig(
            base_os=OS.LINUX,
            lines=lines,
            target=Path("proxmox_bs.ini"),
        )


register.bakery_plugin(
    name="proxmox_bs_local",
    files_function=get_proxmox_bs_local_files,
)
