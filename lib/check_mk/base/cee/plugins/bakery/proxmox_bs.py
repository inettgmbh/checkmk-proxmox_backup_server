#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
import pprint
from pathlib import Path
from typing import Any, Dict

from .bakery_api.v1 import FileGenerator, OS, Plugin, register


def get_proxmox_bs_files(conf: Dict[str, Any]) -> FileGenerator:
    if conf == 'server':
        yield Plugin(base_os=OS.LINUX, source=Path("proxmox_bs"))
    elif conf == 'client':
        yield Plugin(base_os=OS.LINUX, source=Path("proxmox_bs_client"))


register.bakery_plugin(
    name="proxmox_bs",
    files_function=get_proxmox_bs_files,
)
