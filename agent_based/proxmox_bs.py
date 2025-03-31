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
    render
)
from .utils import df
import re
import json

import time
from datetime import datetime

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
            try:
                for e in json.loads(c):
                    group_count = group_count+1
                    total_backups = total_backups+int(e["backup-count"])
            except json.JSONDecodeError:
                pass
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
                yield Metric('verify_none', nr,
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
                    '%s (%s) unknown state %s' % (group, upid, stat)
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









# Check for each single client
def proxmox_bs_gen_clientname(client_json):
    if "comment" in client_json and "backup-id" in client_json:
        return str(client_json["backup-id"]) + "-" + str(client_json["comment"])

def proxmox_bs_clients_discovery(section):
    for n, k, c in proxmox_bs_subsections_discovery(section):
        if n == "proxmox-backup-client snapshot list":
            clients = []

            for client_section in json.loads(c):
                if "comment" in client_section and "backup-id" in client_section:
                    cn = proxmox_bs_gen_clientname(client_section)

                    if not cn in clients:
                        clients.append(cn)

            for client_name in clients:
                yield Service(
                    item=client_name,
                    #labels=[ServiceLabel('pbs/datastore', 'yes')]
                )

            return


# Example JSON output from check
#[
#{
#    "backup-id":"103",
#    "backup-time":1742890730,
#    "backup-type":"vm",
#    "comment":"pfsense01",
#    "files":[
#        {
#            "crypt-mode":"none",
#            "filename":"qemu-server.conf.blob",
#            "size":487
#        },
#        {
#            "crypt-mode":"none",
#            "filename":"drive-scsi0.img.fidx",
#            "size":34359738368
#        },
#        {
#            "crypt-mode":"none",
#            "filename":"index.json.blob",
#            "size":414
#        },
#        {
#            "filename":"client.log.blob"
#        }
#    ],
#    "owner":"user",
#    "protected":false,
#    "size":34359739269
#},
#{
#    "backup-id":"103",
#    "backup-time":1742550846,
#    "backup-type":"vm",
#    "comment":"pfsense01",
#    "files":[
#       {
#           "crypt-mode":"none",
#           "filename":"qemu-server.conf.blob",
#           "size":487
#        },
#        {
#            "crypt-mode":"none",
#            "filename":"drive-scsi0.img.fidx",
#            "size":34359738368
#        },
#        {
#            "crypt-mode":"none",
#            "filename":"index.json.blob",
#            "size":514
#        },
#        {
#            "filename":"client.log.blob"
#        }
#    ],
#    "owner":"user",
#    "protected":false,
#    "size":34359739369,
#    "verification":{
#        "state":"ok",
#        "upid":"UPID:pbs:000002C0:000007BA:00000001:67DE4FC4:verificationjob:fs01\\x3av\\x2dee54fa7e\\x2d61f0:root@pam:"
#    }
#}
#]




def proxmox_bs_clients_checks(item, params, section):
    clients = {}

    #structure results from check output
    for n, k, c in proxmox_bs_subsections_checks(section):
        if (n == "proxmox-backup-client snapshot list"):
            for e in json.loads(c):
                #Get clientname
                cn = proxmox_bs_gen_clientname(e)

                #Only process do fruther processing for current item
                if cn != item:
                    continue

                if not cn in clients:
                    clients[cn] = {}

                #Verification states
                if not "verification" in clients[cn]:
                    clients[cn]["verification"] = {}

                    clients[cn]["verification"]["ok"] = {}
                    clients[cn]["verification"]["ok"]["newest_date"] = None
                    clients[cn]["verification"]["ok"]["count"] = 0

                    clients[cn]["verification"]["failed"] = {}
                    clients[cn]["verification"]["failed"]["newest_date"] = None
                    clients[cn]["verification"]["failed"]["count"] = 0

                    clients[cn]["verification"]["notdone"] = {}
                    clients[cn]["verification"]["notdone"]["newest_date"] = None
                    clients[cn]["verification"]["notdone"]["count"] = 0

                #Backup age
                dt = int(e["backup-time"])

                if "verification" in e:
                    verify_state = e.get("verification", {}).get("state", "na")
                    if verify_state == "ok":
                        clients[cn]["verification"]["ok"]["count"] += 1
                        if clients[cn]["verification"]["ok"]["newest_date"] == None:
                            clients[cn]["verification"]["ok"]["newest_date"] = dt
                        elif clients[cn]["verification"]["ok"]["newest_date"] < dt:
                            clients[cn]["verification"]["ok"]["newest_date"] = dt

                    else:
                        clients[cn]["verification"]["failed"]["count"] += 1
                        if clients[cn]["verification"]["failed"]["newest_date"] == None:
                            clients[cn]["verification"]["failed"]["newest_date"] = dt
                        elif clients[cn]["verification"]["failed"]["newest_date"] < dt:
                            clients[cn]["verification"]["failed"]["newest_date"] = dt
                else:
                        clients[cn]["verification"]["notdone"]["count"] += 1
                        if clients[cn]["verification"]["notdone"]["newest_date"] == None:
                            clients[cn]["verification"]["notdone"]["newest_date"] = dt
                        elif clients[cn]["verification"]["notdone"]["newest_date"] < dt:
                            clients[cn]["verification"]["notdone"]["newest_date"] = dt


            #Process client result and yield results (in the clients array should only be the client matching the item)
            for cn in clients:
                if cn != item: #useless, because filtering for the right item is done above. But leave it there for safty.
                    continue

                #OK
                dpt = ""
                if clients[cn]["verification"]["ok"]["count"] < params["snapshot_min_ok"]:
                    s=State.WARN
                    dpt= " (minimum of %s backups not reached)" % params["snapshot_min_ok"]
                elif clients[cn]["verification"]["ok"]["count"] >= params["snapshot_min_ok"]:
                    s=State.OK
                    dpt= ""

                yield Result(state=s, summary=(
                    'Snapshots verify OK: %d%s' % (clients[cn]["verification"]["ok"]["count"],dpt)
                    ))

                #Age Check OK
                if clients[cn]["verification"]["ok"]["newest_date"] != None:
                    age = int(time.time() - clients[cn]["verification"]["ok"]["newest_date"])

                    warn_age, critical_age = params['bkp_age']

                    if age >= critical_age:
                        s = State.CRIT
                    elif age >= warn_age:
                        s = State.WARN
                    else:
                        s = State.OK

                    yield Result(state=s, summary=(
                        'Timestamp latest verify OK: %s, Age: %s' % (render.datetime(clients[cn]["verification"]["ok"]["newest_date"]), render.timespan(age))
                        ))
                else:
                    s = State.WARN
                    yield Result(state=s, summary=(
                        'Timestamp latest verify OK: No verified snapshot found'
                        ))

                #Not verified
                yield Result(state=State.OK, summary=(
                    'Snapshots verify notdone: %d' % clients[cn]["verification"]["notdone"]["count"]
                    ))

                if clients[cn]["verification"]["notdone"]["newest_date"] != None:
                    age = int(time.time() - clients[cn]["verification"]["notdone"]["newest_date"])

                    yield Result(state=State.OK, summary=(
                        'Timestamp latest unverified: %s, Age: %s' % (render.datetime(clients[cn]["verification"]["notdone"]["newest_date"]), render.timespan(age))
                        ))
                else:
                    s = State.WARN
                    yield Result(state=State.OK, summary=(
                        'Timestamp latest unverified: No unverified snapshot found'
                        ))


                #Failed
                if clients[cn]["verification"]["failed"]["count"] > 0:
                    s=State.CRIT
                else:
                    s=State.OK

                yield Result(state=s, summary=(
                    'Snapshots verify failed: %d' % clients[cn]["verification"]["failed"]["count"]
                    ))


default_proxmox_bs_clients_params={'bkp_age': (172800, 259200), 'snapshot_min_ok': 1}
register.check_plugin(
    name="proxmox_bs_clients",
    service_name="PBS Client %s",
    sections=["proxmox_bs"],
    discovery_function=proxmox_bs_clients_discovery,
    check_function=proxmox_bs_clients_checks,
    check_default_parameters=default_proxmox_bs_clients_params,
    check_ruleset_name="proxmox_bs_clients"
)
