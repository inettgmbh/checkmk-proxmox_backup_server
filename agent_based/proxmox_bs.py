#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

from .agent_based_api.v1 import (
    get_value_store,
    register,
    Metric,
    Service,
    ServiceLabel,
    State,
    Result,
)
from .utils import df
import re
import json

proxmox_bs_subsection_start = re.compile("^===")
proxmox_bs_subsection_int = re.compile("===.*$")
proxmox_bs_subsection_end = re.compile("^=")


def proxmox_bs_subsections_discovery(section):
    active = False

    name = None
    key = None
    content = ""
    key_i = 0

    for line in section:
        line = ' '.join(''.join(_) for _ in line)
        if active and proxmox_bs_subsection_end.match(line):
            active = False
            yield name, key, content
            key = None
            name = None
            content = ""
        if (not active) and proxmox_bs_subsection_start.match(line):
            active = True
            rest = str(line)[3:].strip()
            s_rest = rest.split('===')
            name = s_rest[0]
            if len(s_rest) == 2:
                key = s_rest[1]
                key_i += 1
            content = ""
            continue
        if active:
            content += str(line).rstrip()


def proxmox_bs_subsections_checks(section):
    active = False

    name = None
    key = None
    content = ""
    key_i = 0

    for line in section:
        line = ' '.join(line)
        if active and proxmox_bs_subsection_end.match(line):
            active = False
            yield name, key, content
            key = None
            name = None
            content = ""
        if (not active) and proxmox_bs_subsection_start.match(line):
            active = True
            rest = line[3:].strip()
            s_rest = rest.split('===')
            name = s_rest[0].rstrip()
            if len(s_rest) == 2:
                key = s_rest[1]
                key_i += 1
            content = ""
            continue
        if active:
            content += line.rstrip()


def proxmox_bs_discovery(section):
    for n, k, c in proxmox_bs_subsections_discovery(section):
        if n == "proxmox-backup-manager datastore list":
            for ds in json.loads(c):
                if "name" in ds:
                    yield Service(
                        item=ds["name"],
                        labels=[ServiceLabel('pbs/datastore', 'yes')]
                    )
            return

def proxmox_bs_checks(item, params, section):
    req_ok = True
    expected = []
    missing = []

    upid = None
    upid_status = {}

    gc_ok = False
    gc_running = False

    running_tasks = []
    value_store = get_value_store()

    group_count = 0
    total_backups = 0

    for n, k, c in proxmox_bs_subsections_checks(section):
        if n == "proxmox-backup-manager task list":
            task_list = json.loads(c)
            for task in task_list:
                if ("starttime" in task) and ("endtime" not in task):
                    running_tasks.append(task["upid"])
                    if task.get("worker_id", None) is not None:
                        if task.get("worker_id", None) == item:
                            gc_running = True
        if (
                (n == "proxmox-backup-manager garbage-collection status")
                and (k == item)
            ):
                gc = json.loads(c)
                if "upid" in gc:
                    upid = gc["upid"]
        if (n == "proxmox-backup-client list") and (k == item):
            for e in json.loads(c):
                group_count=group_count+1
                total_backups=total_backups+int(e["backup-count"])
        if (n == "proxmox-backup-client snapshot list") and (k == item):
            nr, np, ok, nok = 0, [], 0, []
            try:
                for e in json.loads(c):
                    if "verification" in e:
                        verify_state = e.get("verification", {}).get("state", "na")
                        if verify_state == "ok":
                            ok = ok+1
                        elif verify_state == "failed":
                            nok.append(e)
                        else:
                            np.append(e)
                    else:
                        nr = nr+1
                yield Metric('group_count', group_count)
                yield Metric('total_backups', total_backups)
                yield Metric('verify_ok', ok)
                yield Metric('verify_failed', len(nok))
                yield Metric('verify_unknown', len(np))
                yield Metric('not_verified_yet', nr,
                    levels=(group_count, group_count*2)
                )
                yield Result(state=State.OK, summary=(
                    'Snapshots Verified: %d' % ok
                    ))
                yield Result(state=State.OK, summary=(
                    'Snapshots not verified yet: %d' % nr
                    ))
            except:
                yield Result(
                    state=State.WARN,
                    summary='snapshot parsing error',
                )
            for e in np:
                group = '%s/%s' % (e["backup-type"], e["backup-id"])
                stat = e["verification"]["state"]
                upid = e["verification"]["upid"]
                yield Result(state=State.UNKN, summary=(
                    '%s (%s) unkown state %s' % (group, upid, stat)
                    ))
            for e in nok:
                group = '%s/%s' % (e["backup-type"], e["backup-id"])
                stat = e["verification"]["state"]
                upid = e["verification"]["upid"]
                yield Result(state=State.CRIT, summary=(
                    'Verification of %s (%s) %s' % (group, upid, stat)
                    ))


        if (n == "proxmox-backup-client status") and (k == item):
            try:
                ds_status = json.loads(c)
                size_mb = int(ds_status["total"])
                avail_mb = int(ds_status["avail"])

                yield from df.df_check_filesystem_single(
                    value_store, item, size_mb, avail_mb,
                    None, None, None, params
                )
            except:
                yield Result(
                    state=State.UNKNOWN,
                    summary="error checking datastore status"
                )
        if (n == "proxmox-backup-manager task log") and (k == upid):
            if "TASK OK" in c.strip()[-7:]:
                gc_ok = True

        if n == "EOD":
            if gc_running:
                yield Result( state=State.OK, summary="GC running" )
            elif gc_ok:
                yield Result( state=State.OK, summary="GC ok" )
            elif upid == None:
                yield Result( state=State.UNKNOWN, summary="GC not run yet" )
            else:
                yield Result( state=State.WARN, summary="GC Task failed" )


register.agent_section(
    name="proxmox_bs",
    #host_label_function = proxmox_bs_hostlabels,
)

register.check_plugin(
    name="proxmox_bs",
    service_name="PBS Datastore %s",
    sections=["proxmox_bs"],
    discovery_function=proxmox_bs_discovery,
    check_function=proxmox_bs_checks,
    check_default_parameters=df.FILESYSTEM_DEFAULT_LEVELS,
    check_ruleset_name="filesystem",
)

