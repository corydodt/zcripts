"""
zcripts
"""

import argparse
from copy import deepcopy
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import subprocess
import sys

import tomlkit


DEFAULT_ZCRIPTS_HOME = Path("/zcriptsinit")
SYSTEMD_HOSTNAME_COMMAND = "hostnamectl hostname"


@dataclass
class Paths:
    """
    A collection of important paths
    """

    zcripts_home: Path
    init_resource_dir: Path
    init_script: Path

    @classmethod
    def from_cli(cls, zcripts_home: str, hostname: str) -> "Paths":
        """
        Build a Paths object from the info we received on the cli and the hostname
        """
        zcripts_home = Path(zcripts_home)
        init_resource_dir = cls.find_resource_dir(zcripts_home, hostname)
        init_script = cls.find_script(init_resource_dir)

        return cls(zcripts_home, init_resource_dir, init_script)

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
    return read_toml(home / "defaults.toml")


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


def main():
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument("--hostname-command", default=SYSTEMD_HOSTNAME_COMMAND, 
                        help="Command that will print a single line with the hostname (default: %(default)s)")
    parser.add_argument("--dump-config-only", action="store_true",
                        help="If true, do nothing except print the toml config (default: %(default)s)")
    parser.add_argument("--first-boot", action="store_true",
                        help="If true, run the first-boot init script (default: %(default)s)")
    parser.add_argument("--ignore-missing-host", action="store_true",
                        help="If true, exit with rc=0 (success) even when no init exists for this hostname (default: %(default)s)")
    parser.add_argument("--zcripts-home", default=DEFAULT_ZCRIPTS_HOME,
                        help="Path to a directory containing host.d and defaults.toml (default: %(default)s)")
    ns = parser.parse_args()

    defaults = read_defaults(ns.zcripts_home)
    hostname = get_hostname(ns.hostname_command)
    paths = Paths.from_cli(ns.zcripts_home, hostname)
    overloads = update_config(defaults, paths.init_resource_dir / "config.toml")

    if ns.dump_config_only:
        print(f"# hostname at runtime: {hostname}")
        print(f"# ZCRIPTS_HOME: {paths.zcripts_home}")
        print(f"# ZCRIPTS_INIT_DIR: {paths.init_resource_dir}")
        print(f"# ZCRIPTS_INIT_SCRIPT: {paths.init_script}")
        print(f"# ZCRIPTS_LIB_BASH: {paths.zcripts_lib_bash}")
        print(tomlkit.dumps(overloads))
        return 0

    if ns.first_boot:
        new_env = deepcopy(os.environ)
        new_env.update(overloads["environment"])
        new_env["ZCRIPTS_HOME"] = str(paths.zcripts_home)
        new_env["ZCRIPTS_LIB_BASH"] = str(paths.zcripts_lib_bash)
        new_env["ZCRIPTS_INIT_DIR"] = str(paths.init_resource_dir)
        new_env["ZCRIPTS_INIT_SCRIPT"] = str(paths.init_script)

        try:
            os.chdir(paths.init_resource_dir)
            os.execle(paths.init_script, paths.init_script, new_env)
        except OSError as e:
            if e.errno == errno.ENOENT:
                if not ns.ignore_missing_host:
                    raise parser.error(f"{paths.init_script}: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
