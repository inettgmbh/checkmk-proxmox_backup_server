# check_mk Plugin for Proxmox Backup Server
[![release](https://github.com/inettgmbh/checkmk-proxmox_backup_server/actions/workflows/release.yml/badge.svg)](https://github.com/inettgmbh/checkmk-proxmox_backup_server/actions/workflows/release.yml)

This check_mk extension adds checks Proxmox Backup Server:
* Datastore (Size, Usage)
* Garbage collection
* Verify jobs

## Warning
This extension is still work in progress and **produces a huge agent output**

## Installation
The mkp archive can be downloaded directly from the [release](https://github.com/inettgmbh/checkmk-proxmox_backup_server/releases/latest) and installed by following the [documentation of check_mk](https://docs.checkmk.com/latest/en/mkps.html).

## Building
Usually you don't see a section as how to build an mkp, because usually it's done like check_mk suggests using [WATO](https://docs.checkmk.com/latest/en/mkps.html#_creating_packages) or [CLI](https://docs.checkmk.com/latest/en/mkps.html#_creating_a_package).
But we made it easier and included two helper tools into this repository, that depend on the tool [python-mkp](https://github.com/inettgmbh/python-mkp), which is a fork of [tom-mi/python-mkp](https://github.com/tom-mi/python-mkp).
Unfortunally, the original tool, which can be installed using `pip` **cannot** be used because it wouldn't package some files.

### Requirements
* python-mkp

just run

```sh
$ build/mkp-pack
```

## Contributing

### issues, you can't fix / ideas, you can't implement

Use GitHub's [Issues](https://github.com/inettgmbh/checkmk-proxmox_backup_server/issues):
Try to explain as clear and short as possible.

### you want to write some code?

* Use Pull requests
* Sign off your commits
* Adapt to the coding style. Divert from it, if doing so increases readability.
* Don't check in IDE specific files or products of a build.

## Issues
yes, we have those
This extension 'works for us' right now, but it's far from optimal.

* Agent output is way to much and must be optimized
* Names of metrics should be changed

## TODOs
(even more, than issues)

* Check of sync jobs
* Check prune jobs
* Check tape jobs
* Check, if verify jobs are running
* Optimize parsing of agent output
* Add check parameters for timeouts of verify, garbage collection and prune jobs
* Move todos and issues to GitHub issues and projects (without being recursive)

