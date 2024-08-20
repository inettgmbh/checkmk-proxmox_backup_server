#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.
from typing import Mapping, Any

from cmk.agent_based.v2 import (
    StringTable,
    DiscoveryResult,
    Service,
    Result,
    State,
    CheckResult,
    AgentSection,
    CheckPlugin,
    Metric,
    ServiceLabel,
    get_value_store,
)
from cmk.plugins.lib.df import df_check_filesystem_single, FILESYSTEM_DEFAULT_LEVELS
import re
import json

proxmox_bs_subsection_start = re.compile("^===")
proxmox_bs_subsection_int = re.compile("===.*$")
proxmox_bs_subsection_end = re.compile("^=")

Section = dict


def parse_proxmox_bs(string_table: StringTable) -> Section:
    parsed = {'tasks': {}, 'data_stores': {}}
    key = ""
    for line in string_table:
        if line == ["="] or line == [""]:
            continue
        elif line[0].startswith("==="):
            key = "_".join(line).strip("=")
            if key.__contains__("===") and not key.__contains__("proxmox-backup-manager_task_log"):
                keys = key.split("===")
                if not parsed['data_stores'].__contains__(keys[1]):
                    parsed['data_stores'][keys[1]] = {keys[0]: {}}
        elif key == "requirements":
            continue
        else:
            if key.__contains__("==="):
                if not key.__contains__("proxmox-backup-manager_task_log"):
                    keys = key.split("===")
                    try:
                        parsed['data_stores'][keys[1]][keys[0]] = json.loads(" ".join(line))
                    except json.decoder.JSONDecodeError:
                        pass
                else:
                    tmp_key = key.split("===")[1]
                    line = " ".join(line)
                    if not parsed['tasks'].__contains__(tmp_key):
                        parsed['tasks'][tmp_key] = {}
                    if line.__contains__(":"):
                        line = line.split(":")
                        parsed['tasks'][tmp_key][line[0]] = line[1]
                    else:
                        if line == "TASK OK":
                            parsed['tasks'][tmp_key]['task_ok'] = True
                        else:
                            parsed['tasks'][tmp_key]['task_ok'] = False
            else:
                try:
                    parsed[key.split("_", 1)[1]] = json.loads(" ".join(line))
                except json.decoder.JSONDecodeError:
                    pass
    return parsed


agent_section_proxmox_bs = AgentSection(
    name="proxmox_bs",
    parse_function=parse_proxmox_bs,
)


def discover_proxmox_bs(section: Section) -> DiscoveryResult:
    for key in section['data_stores'].keys():
        yield Service(
            item=key,
            labels=[ServiceLabel('pbs/datastore', 'yes')],
        )


def check_proxmox_bs(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    data_store = section['data_stores'][item]

    running_tasks = []
    gc_running = False
    for task in section['task_list']:                                                                   # proxmox-backup-manager task list
        if "starttime" in task and "endtime" not in task:
            running_tasks.append(task['upid'])
            if task.get('worker_id', None) is not None and task['worker_id'].__contains__(item):
                gc_running = True

    garbage_collection = data_store['proxmox-backup-manager_garbage-collection_status']                 # proxmox-backup-manager garbage-collection status
    upid = None
    if garbage_collection.get('upid', None) is not None:
        upid = garbage_collection['upid']
    if len(data_store.keys()) != 4:
        yield Result(
            state=State.CRIT,
            summary=f"Authorization failed. Please check to make sure the Given Credentials were correct."
        )
        return
    b_list = data_store['proxmox-backup-client_list']                                                   # proxmox-backup-client list
    group_count = 0
    total_backups = 0
    for e in b_list:
        group_count += 1
        total_backups += int(e['backup-count'])

    yield Metric(
        name="group_count",
        value=group_count,
    )
    yield Metric(
        name="total_backups",
        value=total_backups,
    )

    snapshot_list = data_store['proxmox-backup-client_snapshot_list']                                   # proxmox-backup-client snapshot list
    nr, np, ok, nok = 0, [], 0, []
    for e in snapshot_list:
        if e.get("verification", None) is not None:
            verify_state = e['verification'].get("state", "na")
            if verify_state == "ok":
                ok += 1
            elif verify_state == "failed":
                nok.append(e)
            else:
                np.append(e)
        else:
            nr += 1

    yield Metric(
        name="verify_ok",
        value=ok,
    )
    yield Metric(
        name="verify_failed",
        value=len(nok),
    )
    yield Metric(
        name="verify_unknown",
        value=len(np)
    )
    yield Metric(
        name="verify_none",
        value=nr,
        levels=(group_count, group_count * 2)
    )
    yield Result(
        state=State.OK,
        summary=f"Snapshots Verified: {ok}"
    )
    yield Result(
        state=State.OK,
        summary=f"Snapshots not verified yet: {nr}"
    )

    for e in np:
        group = f"{e['backup-type']}/{e['backup-id']}"
        stat = e['verification']['state']
        upid = e['verification']['upid']
        yield Result(
            state=State.UNKNOWN,
            summary=f"{group} ({upid}) unknown state {stat}"
        )
    for e in nok:
        group = f"{e['backup-type']}/{e['backup-id']}"
        stat = e['verification']['state']
        upid = e['verification']['upid']
        yield Result(
            state=State.CRIT,
            summary=f"Verification of {group} ({upid}) {stat}",
        )

    status = data_store['proxmox-backup-client_status']                                                 # proxmox-backup-client status

    try:
        size_mb = float(status['total'])
        avail_mb = float(status['avail'])
        value_store = get_value_store()

        yield from df_check_filesystem_single(
            value_store=value_store,
            mountpoint=item,
            filesystem_size=size_mb,
            free_space=avail_mb,
            reserved_space=None,
            inodes_total=None,
            inodes_avail=None,
            params=params,
            this_time=None,
        )
    except:
        yield Result(
            state=State.UNKNOWN,
            summary=f"error checking datastore status"
        )

    gc_ok = False
    if section['tasks'].get(upid, None) is not None:                                                    # proxmox-backup-manager task log
        gc_ok = section['tasks'][upid].get('task_ok', False)

    if gc_running:
        yield Result(
            state=State.OK,
            summary=f"GC running",
        )
    elif gc_ok:
        yield Result(
            state=State.OK,
            summary=f"GC ok"
        )
    elif upid is None:
        yield Result(
            state=State.UNKNOWN,
            summary=f"GC not run yet",
        )
    else:
        yield Result(
            state=State.WARN,
            summary=f"GC Task failed",
        )


check_plugin_proxmox_bs = CheckPlugin(
    name="proxmox_bs",
    service_name="PBS Datastore %s",
    sections=["proxmox_bs"],
    discovery_function=discover_proxmox_bs,
    check_function=check_proxmox_bs,
    check_default_parameters=FILESYSTEM_DEFAULT_LEVELS,
    check_ruleset_name="filesystem",
)
