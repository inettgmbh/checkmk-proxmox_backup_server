#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2021 inett GmbH
# License: GNU General Public License v2
# A file is subject to the terms and conditions defined in the file LICENSE,
# which is part of this source code package.

import datetime
import time
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
    RuleSetType,
    Metric,
    ServiceLabel,
    get_value_store,
)
from cmk.plugins.lib.df import df_check_filesystem_single, FILESYSTEM_DEFAULT_LEVELS
import re
import json

Section = dict


def parse_proxmox_bs(string_table: StringTable) -> Section:
    parsed = {
        "data-stores": {},
        "sync-jobs": {},
        "running-tasks": [],
    }
    key = ""
    for line in string_table:
        line = ''.join(line)
        if line.startswith(">") and line.endswith("<"):
            key = line[1:-1]
        else:
            dict_line = json.loads(line)
            match key:
                case "sync-jobs":
                    parsed[key][dict_line['id']] = dict_line
                case "data-stores":
                    parsed[key][dict_line['store']] = dict_line
                case "running-tasks":
                    parsed[key] = dict_line

    return parsed


agent_section_proxmox_bs = AgentSection(
    name="proxmox_bs",
    parse_function=parse_proxmox_bs,
)


def discover_proxmox_bs(params: Mapping[str, Any], section: Section) -> DiscoveryResult:
    def _prepare_service(item: str) -> Service:
        return Service(
            item=item,
            labels=[ServiceLabel("pbs/datastore", "yes")],
        )

    def _yield_services(condition, seperate_namespaces, cond_arg=None) -> DiscoveryResult:
        for datastore in section['data-stores'].keys():
            if condition(datastore, cond_arg):
                if seperate_namespaces:
                    yield _prepare_service(f"{datastore} Namespace ROOT")
                    for namespace in section['data-stores'][datastore]['namespace']:
                        yield _prepare_service(f"{datastore} Namespace {namespace['namespace']}")
                else:
                    yield _prepare_service(datastore)

    filter_param = params['filter'] if params['filter'] is not None else {}
    match filter_param.get('datastores', ('all', 'all')):
        case ('regex', regex):
            regex = re.compile(regex)
            match filter_param.get('limit_key', ('name', 'name'))[1]:
                case 'name':
                    yield from _yield_services(
                        (lambda x, y: y.match(x)),
                        params.get('seperate_namespaces', False),
                        regex,
                    )
                case _:
                    yield from _yield_services(
                        (lambda x, y: y.match(section['data-stores'][x]['path'])),
                        params.get('seperate_namespaces', False),
                        regex,
                    )
        case ('selected', selection):
            selection = selection.split('\\n')
            match filter_param.get('limit_key', ('name', 'name'))[1]:
                case 'name':
                    yield from _yield_services(
                        (lambda x, y: x in y),
                        params.get('seperate_namespaces', False),
                        selection,
                    )
                case _:
                    yield from _yield_services(
                        (lambda x, y: section['data-stores'][x]['path'] in y),
                        params.get('seperate_namespaces', False),
                        selection,
                    )
        case _:
            yield from _yield_services(lambda x, y: True, params.get('seperate_namespaces', False))


def check_proxmox_bs(item: str, params: Mapping[str, Any], section: Section) -> CheckResult:
    def _read_backup_stats(obj: Mapping[str, Any], namespace: str) -> Mapping[str, Any]:
        result = {
            'backups': 0,
            'groups': len(obj['groups']),
            'ok': obj['verification']['ok'],
            'fail': obj['verification']['fail'],
            'fail_list': obj['verification']['fail_list'],
            'not_verified': obj['verification']['not_verified'],
            'unknown_state': obj['verification']['unknown_state'],
            'unknown_state_list': obj['verification']['unknown_state_list'],
        }
        for group in obj['groups']:
            result['backups'] += group['backup-count']
        for fail in result['fail_list']:
            fail['namespace'] = namespace
        for unknown in result['unknown_state_list']:
            unknown['namespace'] = namespace
        return result

    items = item.split(" Namespace ", 1)
    datastore = section['data-stores'].get(items[0], {})
    if datastore == {}:
        return

    gc_running = any(
        task['worker-type'] == "garbage_collection" and task['worker-id'].__contains__(datastore['store'])
        for task in section['running-tasks']
    )

    backup_stats = {
        v['namespace']: _read_backup_stats(v, v['namespace']) for v in datastore['namespace']
    }
    backup_stats['ROOT'] = _read_backup_stats(datastore, 'ROOT')

    if len(items) == 2:
        namespace = items[1]
        stats = backup_stats[namespace]
        yield from _yield_backup_metrics(stats)

        if stats['ok']:
            yield Result(
                state=State.OK,
                summary=f"Snapshots verified: {stats['ok']}",
            )

        if stats['not_verified']:
            yield Result(
                state=State.OK,
                summary=f"Snapshots not verified yet: {stats['not_verified']}",
            )

        if stats['fail']:
            yield Result(
                state=State.CRIT,
                summary=f"Verification of {stats['fail']} snapshots failed",
            )

        if stats['unknown_state']:
            yield Result(
                state=State.CRIT,
                summary=f"Verification of {stats['unknown']} is in a unknown state",
            )

        yield Result(
            state=State.OK,
            summary=f"Snapshots: {stats['backups']}"
        )

        yield Result(
            state=State.OK,
            summary=f"Snapshot Groups: {stats['groups']}"
        )

    else:
        backup_stats_combined = {
            'backups': 0,
            'groups': 0,
            'ok': 0,
            'fail': 0,
            'fail_list': [],
            'not_verified': 0,
            'unknown_state': 0,
            'unknown_state_list': [],
        }
        for e in backup_stats.keys():
            for k, v in backup_stats[e].items():
                backup_stats_combined[k] += v

        yield from _yield_backup_metrics(backup_stats_combined)

        if backup_stats_combined['ok']:
            yield Result(
                state=State.OK,
                summary=f"Snapshots verified: {backup_stats_combined['ok']}",
                details="\n".join([f"Snapshots verified in namespace {k}:  {v['ok']}" for k, v in backup_stats.items()]),
            )

        if backup_stats_combined['not_verified']:
            yield Result(
                state=State.OK,
                summary=f"Snapshots not verified yet: {backup_stats_combined['not_verified']}",
                details="\n".join([f"Snapshots not verified yet in namespace {k}:  {v['not_verified']}"
                                   for k, v in backup_stats.items()]),
            )

        if backup_stats_combined['fail']:
            yield Result(
                state=State.CRIT,
                summary=f"Verification of {backup_stats_combined['fail']} snapshots failed",
                details="\n".join([f"Verification of Snapshot {v['backup-id']} in Namespace {v['namespace']} ({v['verification-upid']}):  {v['verification-state']}"
                                   for v in backup_stats_combined['fail_list']]),
            )

        if backup_stats_combined['unknown_state']:
            yield Result(
                state=State.CRIT,
                summary=f"Verification of {backup_stats_combined['unknown']} is in a unknown state",
                details="\n".join([f"Verification of Snapshot {v['backup-id']} in Namespace {v['namespace']} ({v['verification-upid']}):  {v['verification-state']}"
                                   for v in backup_stats_combined['unknown_state_list']]),
            )

        yield Result(
            state=State.OK,
            summary=f"Snapshots: {backup_stats_combined['backups']}"
        )

        yield Result(
            state=State.OK,
            summary=f"Snapshot Groups: {backup_stats_combined['groups']}"
        )

    if len(items) == 1 or items[1] == "ROOT":
        size = float(datastore['status']['total']) / 1024.0 / 1024.0
        avail = float(datastore['status']['avail']) / 1024.0 / 1024.0
        value_store = get_value_store()

        yield from df_check_filesystem_single(
            value_store=value_store,
            mountpoint=item,
            filesystem_size=size,
            free_space=avail,
            reserved_space=0,
            inodes_total=None,
            inodes_avail=None,
            params=params,
            this_time=None,
        )

        if gc_running:
            yield Result(
                state=State.OK,
                summary=f"GC running",
            )
        elif datastore['gc']['last-run-state'] == "OK":
            yield Result(
                state=State.OK,
                summary="GC OK"
            )
        elif datastore['gc']['upid'] is None:
            yield Result(
                state=State.UNKNOWN,
                summary="GC has not run yet",
            )
        else:
            yield Result(
                state=State.WARN,
                summary="GC Task failed",
            )


def _yield_backup_metrics(backup_stats: Mapping[str, Any]) -> CheckResult:
    yield Metric(
        name="proxmox_bs_group_count",
        value=backup_stats['groups'],
    )
    yield Metric(
        name="proxmox_bs_backup_count",
        value=backup_stats['backups'],
    )
    yield Metric(
        name="proxmox_bs_verify_ok",
        value=backup_stats['ok'],
    )
    yield Metric(
        name="proxmox_bs_verify_fail",
        value=backup_stats['fail'],
    )
    yield Metric(
        name="proxmox_bs_verify_unknown",
        value=backup_stats['unknown_state'],
    )
    yield Metric(
        name="proxmox_bs_verify_none",
        value=backup_stats['not_verified'],
        levels=(backup_stats["groups"], backup_stats["groups"] * 2)
    )


check_plugin_proxmox_bs = CheckPlugin(
    name="proxmox_bs",
    service_name="PBS Datastore %s",
    sections=["proxmox_bs"],
    discovery_function=discover_proxmox_bs,
    check_function=check_proxmox_bs,
    check_default_parameters=FILESYSTEM_DEFAULT_LEVELS,
    check_ruleset_name="filesystem",
    discovery_ruleset_name="proxmox_bs_discovery",
    discovery_ruleset_type=RuleSetType.MERGED,
    discovery_default_parameters={
        "filter": None,
        "seperate_namespaces": False
    },
)


def discover_proxmox_bs_sync_jobs(section: Section) -> DiscoveryResult:
    for key in section["sync-jobs"].keys():
        yield Service(
            item=key,
            labels=[ServiceLabel("pbs/datastore", "yes")],
        )


def check_proxmox_bs_sync_jobs(
    item: str, params: Mapping[str, Any], section: Section
) -> CheckResult:
    sync_job = section["sync-jobs"][item]
    cur_time = int(time.time())
    age_levels = params["age_levels"]

    value_store = get_value_store()

    last_run_state = sync_job.get("last-run-state", "Unknown")
    last_run_endtime = sync_job.get("last-run-endtime", 0)

    if last_run_state == "OK":
        value_store["last_successful_run_endtime"] = last_run_endtime

    yield Result(
        state=State.OK,
        summary=f"Remote PBS: {sync_job.get('remote', 'Unknown')}" if sync_job.get('remote', 'Unknown') is not None
        else f"Local Sync-Job",
    )

    yield Result(
        state=State.OK,
        summary=f"Last Sync-Job time: {datetime.datetime.fromtimestamp(last_run_endtime)}",
    )

    yield Result(
        state=State.OK,
        summary=f"Last Sync-Job status: {last_run_state}",
    )

    if cur_time - int(age_levels[1][1]) > value_store.get("last_successful_run_endtime", 0):
        yield Result(
            state=State.CRIT,
            summary="No recent Sync-Job ended successfully",
        )
    elif cur_time - int(age_levels[1][0]) > value_store.get("last_successful_run_endtime", 0):
        yield Result(
            state=State.WARN,
            summary="No recent Sync-Job ended successfully",
        )


check_plugin_proxmox_bs_sync_jobs = CheckPlugin(
    name="proxmox_bs_sync_jobs",
    service_name="PBS Sync-Job %s",
    sections=["proxmox_bs"],
    discovery_function=discover_proxmox_bs_sync_jobs,
    check_function=check_proxmox_bs_sync_jobs,
    check_default_parameters={
        "age_levels": ("fixed", (86400.0 * 1.1, 86400.0 * 4.1))
    },
    check_ruleset_name="proxmox_bs_sync_jobs",
)


def check_proxmox_bs_snapshots(
    item: str, params: Mapping[str, Any], section: Section
) -> CheckResult:
    date_now = datetime.datetime.now(tz=datetime.timezone.utc)

    items = item.split(" Namespace ", 1)
    datastore = section['data-stores'][items[0]]
    if len(items) == 2:
        namespace = datastore if items[1] == "ROOT" else next(x for x in datastore['namespace'] if x['namespace'] == items[1])
        groups = namespace['groups']
    else:
        groups = datastore['groups']
        for namespace in datastore['namespace']:
            groups.extend(namespace['groups'])

    backup_states = {'ok': [], 'warn': [], 'crit': [], 'ignored': []}

    max_err_age = params.get('ignore_old_errors', None)


    for group in groups:
        last_snapshot_time = datetime.datetime.fromtimestamp(group['last-backup'], tz=datetime.timezone.utc)
        diff = (date_now - last_snapshot_time).total_seconds()
        if params['age_levels'] is not None:
            if max_err_age is not None and diff > max_err_age:
                backup_states['ignored'].append((group, diff))
            elif diff > params['age_levels'][1][1]:
                backup_states['crit'].append((group, diff))
            elif diff > params['age_levels'][1][0]:
                backup_states['warn'].append((group, diff))
            else:
                backup_states['ok'].append((group, diff))
        else:
            backup_states['ok'].append((group, diff))

    details = []

    def _create_detail(x: Mapping[str, Any], age: float, level: str) -> str:
        return (f"State: {level} — " +
        f"ID: {x['backup-id']} — " +
        f"last successful backup: {datetime.datetime.fromtimestamp(x['last-backup'], tz=datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} " +
        f"({round(age / 86400.0, 0)} days ago).\n")

    details.extend([_create_detail(group[0], group[1], "CRITICAL") for group in backup_states['crit']])
    details.extend([_create_detail(group[0], group[1], "WARNING") for group in backup_states['warn']])
    details.extend([_create_detail(group[0], group[1], "IGNORED") for group in backup_states['ignored']])

    def _err_summary_result(num_err: int, threshold: int, err_state: State, throw_warnings: bool) -> Result:
        return Result(
            state=err_state if throw_warnings else State.OK,
            summary=(f"{num_err} Backup{"s" if num_err > 1 else ""} older than " +
                    f"{threshold} " +
                    f"day{"s" if threshold > 1 else ""} within the Datastore"),
        )
    num_crit = len(backup_states['crit'])
    num_warn = len(backup_states['warn'])
    if num_crit > 0:
        yield _err_summary_result(num_crit, int(params["age_levels"][1][1] / 86400.0), State.CRIT, params['throw_warnings'])
    if num_warn > 0:
        yield _err_summary_result(num_warn, int(params["age_levels"][1][0] / 86400.0), State.WARN, params['throw_warnings'])

    if num_crit + num_warn == 0:
        yield Result(
            state=State.OK,
            summary="No issues within the Datastore",
        )

    yield Result(
        state=State.OK,
        summary=f"{len(groups)} Host{"s" if len(groups) > 0 else ""} within the Datastore.",
        details=None if len(details) == 0 else "".join(details),
    )


check_plugin_proxmox_bs_snapshot_age = CheckPlugin(
    name="proxmox_bs_snapshot_age",
    sections=["proxmox_bs"],
    service_name="PBS Datastore Backup Status: %s",
    discovery_function=discover_proxmox_bs,
    check_function=check_proxmox_bs_snapshots,
    check_ruleset_name="proxmox_bs_snapshot_age",
    check_default_parameters={
        "throw_warnings": False,
        "age_levels": ("fixed", (
            2.0 * 24.0 * 60.0 * 60.0 + 60.0 * 60.0 * 2.0,
            10.0 * 24.0 * 60.0 * 60.0 + 60.0 * 60.0 * 2.0
        )),
    },
    discovery_ruleset_name="proxmox_bs_snapshot_age_discovery",
    discovery_ruleset_type=RuleSetType.MERGED,
    discovery_default_parameters={
        "filter": None,
        "seperate_namespaces": False
    },
)
