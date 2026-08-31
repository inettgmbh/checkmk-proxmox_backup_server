# which is part of this source code package.

# -*- encoding: utf-8; py-indent-offset: 4 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from collections.abc import Iterator
from typing import Literal

from pydantic import BaseModel
from cmk.server_side_calls.v1 import SpecialAgentConfig, Secret, HostConfig, SpecialAgentCommand, replace_macros


class Params(BaseModel):
    username: str | None = None
    password: Secret | None = None
    port: int | None = None
    host: (
            tuple[Literal["host_name"], None]
            | tuple[Literal["ip_address"], None]
            | tuple[Literal["custom"], str]
            | None
    ) = None
    no_cert_check: bool = False
    timeout: int | None = None
    cache_time: int | None = None


def commands_function(
        params: Params,
        host_config: HostConfig,
) -> Iterator[SpecialAgentCommand]:
    def host_specifier() -> str:
        if params.host and params.host[0] == "host_name":
            return host_config.name
        if params.host and params.host[0] == "ip_address":
            return host_config.primary_ip_config.address
        if params.host and params.host[0] == "custom":
            return replace_macros(params.host[1], host_config.macros)
        return host_config.name or host_config.primary_ip_config.address

    command_arguments: list[str | Secret] = []
    if params.username is not None:
        command_arguments += ["-u", params.username]
    if params.password is not None:
        command_arguments += ["--password", params.password]
    if params.port is not None:
        command_arguments += ["--port", str(params.port)]
    if params.no_cert_check:
        command_arguments += ["--no-cert-check"]
    if params.timeout is not None:
        command_arguments += ["--timeout", str(params.timeout)]
    if params.cache_time is not None:
        command_arguments += ["--cache-time", str(params.cache_time)]
    command_arguments.append(host_specifier())
    yield SpecialAgentCommand(command_arguments=command_arguments)


special_agent_proxmox_bs = SpecialAgentConfig(
    name="proxmox_bs",
    parameter_parser=Params.model_validate,
    commands_function=commands_function,
)
