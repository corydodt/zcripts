"""
zcripts
"""

import argparse
from copy import deepcopy
from dataclasses import dataclass
import errno
from importlib import metadata
from inspect import cleandoc
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import tomlkit

import questionary

from zcripts.template import *
from zcripts import featureflag as ff


DEFAULT_ZCRIPTS_HOME = Path("/zcriptsinit")
DEFAULT_UNIT_FILE_PATH = Path("/etc/systemd/system")
DEFAULT_CONFIG_PATH = Path("/etc/zcripts")
SYSTEMD_HOSTNAME_COMMAND = "hostnamectl hostname"
SYSTEMD_ESCAPE_COMMAND = "systemd-escape"
## TIMEOUT_COMMAND = "/usr/bin/timeout"


@dataclass
class Paths:
    """
    A collection of important paths
    """

    zcripts_home: Path
    base_resource_dir: Path
    base_script: Path
    init_resource_dir: Path
    init_script: Path

    @classmethod
    def from_cli(cls, zcripts_home: str, hostname: str) -> "Paths":
        """
        Build a Paths object from the info we received on the cli and the hostname
        """
        zcripts_home = Path(zcripts_home)
        base_resource_dir = zcripts_home / "base"
        base_script = cls.find_script(base_resource_dir)
        init_resource_dir = cls.find_resource_dir(zcripts_home, hostname)
        init_script = cls.find_script(init_resource_dir)

        return cls(zcripts_home, base_resource_dir, base_script, init_resource_dir, init_script)

    @property
    def zcripts_lib_bash(self) -> Path:
        return self.zcripts_home / "lib" / "bash"

    @staticmethod
    def find_resource_dir(zcripts_home: Path, hostname: str) -> Path:
        """
        Attempt several variations of the hostname to find a resource dir for this host
        """
        hostd = zcripts_home / "host.d"
        match_exact = hostd.glob(f"{hostname}")
        match_prefix = hostd.glob(f"{hostname}.*")
        match_zcripts_exact = hostd.glob(f"zcripts.{hostname}")
        match_zcripts_prefix = hostd.glob(f"zcripts.{hostname}.*")
        for tries in (
            match_exact,
            match_prefix,
            match_zcripts_exact,
            match_zcripts_prefix,
        ):
            for item in tries:
                if item.is_dir():
                    return item

        # if we reached this point, we didn't find anything. return the exact
        # path we tried first and let upstream report File Not Found.
        return hostd / hostname

    @staticmethod
    def find_script(init_resource_dir: Path) -> Path:
        """
        Search a few known locations for an init script to run on this host
        """
        for test in ["init", "init.py"]:
            attempt = init_resource_dir / test
            if attempt.exists():
                return attempt


def read_defaults(home: Path):
    """
    Read /zcriptsinit/defaults.toml
    """
    ret = read_toml(home / "defaults.toml")
    ret.setdefault("environment", {})
    return ret


def read_toml(filepath: Path):
    """
    Read a toml file, ignoring it if it doesn't exist
    """
    if not filepath.exists():
        return {}

    with filepath.open("rb") as f:
        data = tomlkit.load(f)

    return data


def update_config(config, toml_path: Path):
    """
    Update the config we read from defaults.toml with config that lives in
    host.d/.../config.toml (the specified path argument)
    """
    clone = deepcopy(config)
    clone.update(read_toml(toml_path))
    return clone


def get_hostname(cmd):
    """
    Interact with system services to get the hostname at the moment zcripts runs

    We have to get hostname ourselves because systemd's %H is useless
    in cloud scenarios where the hostname changes after boot.
    """
    return subprocess.getoutput(cmd)


def build_boot(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.description = do_boot.__doc__
    parser.add_argument(
        "--ignore-missing-host",
        action="store_true",
        help="If true, exit with rc=0 (success) even when no init exists for this hostname (default: %(default)s)",
    )
    return parser


def build_dumpconfig(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.description = do_dumpconfig.__doc__
    return parser


## def exec_init_script(exe_path: Path, env, timeout: str="0"):
##     os.execle(TIMEOUT_COMMAND, timeout, exe_path, env)
## 

def do_boot(namespace: argparse.Namespace):
    """
    Run the init script for this host (usually at first boot)
    """
    ns = namespace
    new_env = deepcopy(os.environ)
    new_env.update(ns.overloads["environment"])
    new_env["ZCRIPTS_HOME"] = str(ns.paths.zcripts_home)
    new_env["ZCRIPTS_LIB_BASH"] = str(ns.paths.zcripts_lib_bash)
    new_env["ZCRIPTS_INIT_DIR"] = str(ns.paths.init_resource_dir)
    new_env["ZCRIPTS_INIT_SCRIPT"] = str(ns.paths.init_script)

    try:
        os.chdir(ns.paths.init_resource_dir)
        ## exec_init_script(ns.paths.init_script, ns.main.timeout, new_env)
        os.execle(ns.paths.init_script, ns.paths.init_script, new_env)
    except OSError as e:
        if e.errno == errno.ENOENT:
            if not ns.ignore_missing_host:
                raise ns.subparser.error(f"{ns.paths.init_script}: {e}")

    return 0


def do_dumpconfig(namespace: argparse.Namespace):
    """
    Just print the toml config, then exit
    """
    ns = namespace
    print(f"# hostname at runtime: {ns.hostname}")
    print(f"# ZCRIPTS_HOME: {ns.paths.zcripts_home}")
    print(f"# ZCRIPTS_INIT_DIR: {ns.paths.init_resource_dir}")
    print(f"# ZCRIPTS_INIT_SCRIPT: {ns.paths.init_script}")
    print(f"# ZCRIPTS_LIB_BASH: {ns.paths.zcripts_lib_bash}")
    print(tomlkit.dumps(ns.overloads))
    return 0


def systemd_escape(s: str) -> str:
    """
    Escape `s' with `systemd-escape -p <s>`, for use as a mount point path
    """
    return subprocess.getoutput(f"{SYSTEMD_ESCAPE_COMMAND} --path {s}")


def generate_systemd_strings(answers: dict) -> dict:
    """
    Interpolate configuration into our systemd unit templates and config file.

    Produces a dict of {basename: contents} for each basename of each generated file.
    """
    escaped_mount_point = systemd_escape(answers["mount_point"])
    return {
        "zcripts.service": ZCRIPTS_SERVICE.format(vars=answers),
        f"{escaped_mount_point}.mount": ZCRIPTSINIT_MOUNT.format(vars=answers),
        "answers.toml": tomlkit.dumps({"main": answers}),
    }


def do_generate_systemd(namespace: argparse.Namespace):
    """
    Create unit files you can install to make this instance run zcripts at boot.
    """
    asking_questions = False
    if not namespace.answer_file:
        asking_questions = True
    else:
        try:
            with open(namespace.answer_file) as f:
                answers = tomlkit.load(f)["main"]
        except OSError as e:
            if namespace.answer_file_ignore_missing:
                print(f"** Warning: {e}")
                asking_questions = True
            else:
                raise namespace.subparser.error(e)

    if asking_questions:
        required = lambda text: True if len(text) > 0 else "Required"
        answers = questionary.form(
            fileshare=questionary.text(
                "Path to a fileshare we can mount (e.g. //fileshare/zcriptsinit)?",
                validate=required,
            ),
            mount_point=questionary.path(
                "Where should zcriptsinit be mounted in the filesystem?",
                default=namespace.zcripts_home,
                validate=required,
            ),
        ).unsafe_ask()

    with tempfile.TemporaryDirectory(prefix="zcripts-generate-systemd") as td:
        p = Path(td)

        strings = generate_systemd_strings(answers)
        for basename, contents in strings.items():
            pb = p / basename
            pb.write_text(contents)

        def copy_fn(src, dst, *a, **kw):
            """Verbosely copy"""
            shutil.copy2(src, dst, *a, **kw)
            print(f"Created {dst}")

        shutil.copytree(p, ".", copy_function=copy_fn, dirs_exist_ok=True)


def build_generate_systemd(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.description = do_generate_systemd.__doc__
    parser.add_argument(
        "--answer-file",
        default=None,
        help="Generate files without prompting by loading the given .toml file",
    )
    parser.add_argument(
        "--answer-file-ignore-missing",
        default=None,
        help="If --answer-file is given but the file is missing, just ask the questions instead",
        action="store_true",
    )

    return parser


def build_root_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument(
        "--hostname-command",
        default=SYSTEMD_HOSTNAME_COMMAND,
        help="Specify an external command that will print this hostname, as a single line (default: %(default)s)",
    )
    parser.add_argument(
        "--zcripts-home",
        default=DEFAULT_ZCRIPTS_HOME,
        help="Path to a directory containing host.d and defaults.toml (default: %(default)s)",
        type=Path,
    )
    parser.add_argument(
        "--version", action="version", version=f"zcripts v{metadata.version('zcripts')}"
    )

    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    boot = subparsers.add_parser("boot")
    boot = build_boot(boot)
    boot.set_defaults(sub=do_boot, subparser=boot)
    dumpconfig = subparsers.add_parser("dumpconfig")
    dumpconfig = build_dumpconfig(dumpconfig)
    dumpconfig.set_defaults(sub=do_dumpconfig, subparser=dumpconfig)
    generate_systemd = subparsers.add_parser("generate-systemd")
    generate_systemd = build_generate_systemd(generate_systemd)
    generate_systemd.set_defaults(sub=do_generate_systemd, subparser=generate_systemd)
    return parser


def main():
    parser = build_root_parser()
    ns = parser.parse_args()

    try:
        defaults = read_defaults(ns.zcripts_home)
    except tomlkit.exceptions.InvalidNumberError as e:
        raise ns.subparser.error(f"{ns.zcripts_home / 'defaults.toml'}: {e}")

    setattr(ns, "hostname", get_hostname(ns.hostname_command))
    setattr(ns, "paths", Paths.from_cli(ns.zcripts_home, ns.hostname))
    try:
        setattr(
            ns,
            "overloads",
            update_config(defaults, ns.paths.init_resource_dir / "config.toml"),
        )
    except tomlkit.exceptions.InvalidNumberError as e:
        raise ns.subparser.error(f"{ns.paths.init_resource_dir / 'config.toml'}: {e}")

    return ns.sub(ns)


if __name__ == "__main__":
    sys.exit(main())
