"""
zcripts
"""

import argparse
from copy import deepcopy
from dataclasses import dataclass
import errno
import os
from pathlib import Path
import sys

import tomlkit


DEFAULT_ZCRIPTS_HOME = Path("/zcriptsinit")


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
        zcripts_home = Path(zcripts_home)
        init_resource_dir = cls.find_resource_dir(zcripts_home, hostname)
        init_script = cls.find_script(init_resource_dir)

        return cls(zcripts_home, init_resource_dir, init_script)

    @staticmethod
    def find_resource_dir(zcripts_home: Path, hostname: str) -> Path:
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
        for test in ["init", "init.py"]:
            attempt = init_resource_dir / test
            if attempt.exists():
                return attempt


def read_defaults(home: Path):
    return read_toml(home / "defaults.toml")


def read_toml(filepath: Path):
    if not filepath.exists():
        return {}

    with filepath.open("rb") as f:
        data = tomlkit.load(f)

    return data


def update_config(config, toml_path: Path):
    clone = deepcopy(config)
    clone.update(read_toml(toml_path))
    return clone


def main():
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument("hostname")
    parser.add_argument("--dump-config-only", action="store_true")
    parser.add_argument("--first-boot", action="store_true")
    parser.add_argument("--ignore-missing-host", action="store_true")
    parser.add_argument("--zcripts-home", default=DEFAULT_ZCRIPTS_HOME)
    ns = parser.parse_args()

    defaults = read_defaults(ns.zcripts_home)
    paths = Paths.from_cli(ns.zcripts_home, ns.hostname)
    overloads = update_config(defaults, paths.init_resource_dir / "config.toml")

    if ns.dump_config_only:
        print(tomlkit.dumps(overloads))
        return 0

    if ns.first_boot:
        new_env = deepcopy(os.environ)
        new_env.update(overloads["environment"])
        new_env["ZCRIPTS_HOME"] = str(paths.zcripts_home)
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
