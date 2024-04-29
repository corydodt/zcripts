"""
zcripts
"""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import sys

import tomlkit


DEFAULT_ZCRIPTS_HOME = Path("/zcriptsinit")


def find_script(where: Path, hostname: str):
    hostd = where / "host.d"
    match_exact = hostd.glob(f"{hostname}")
    match_prefix = hostd.glob(f"{hostname}.*")
    match_zcripts_exact = hostd.glob(f"zcripts.{hostname}")
    match_zcripts_prefix = hostd.glob(f"zcripts.{hostname}.*")
    for tries in match_exact, match_prefix, match_zcripts_exact, match_zcripts_prefix:
        for item in tries:
            return item
    
    # if we reached this point, we didn't find anything. return the exact
    # path we tried first and let upstream report File Not Found.
    return hostd / hostname


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
    parser.add_argument("--first-boot", nargs=1, metavar="HOSTNAME")
    parser.add_argument("--zcripts-home", nargs=1, default=DEFAULT_ZCRIPTS_HOME)
    parser.add_argument("--dump-config-only", action="store_true")
    ns = parser.parse_args()

    defaults = read_defaults(ns.zcripts_home)

    if ns.first_boot:
        script_path = find_script(ns.zcripts_home, ns.first_boot[0])
        overloads = update_config(defaults, script_path.with_suffix(script_path.suffix + ".toml"))

        if ns.dump_config_only:
            print(tomlkit.dumps(overloads))
            return 0

        new_env = deepcopy(os.environ)
        new_env.update(overloads["environment"])

        try:
            os.execle(script_path, script_path, new_env)
        except OSError as e:
            raise parser.error(f"{script_path}: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
