"""
zcripts
"""

import argparse
import glob
import os
import sys

DEFAULT_ZCRIPTS_PATH = "/zcriptsinit/host.d"

def find_script(where, hostname):
    match_exact = glob.glob(f"{where}/{hostname}")
    match_prefix = glob.glob(f"{where}/{hostname}.*")
    match_zcripts_exact = glob.glob(f"{where}/zcripts.{hostname}")
    match_zcripts_prefix = glob.glob(f"{where}/zcripts.{hostname}.*")
    for tries in match_exact, match_prefix, match_zcripts_exact, match_zcripts_prefix:
        if len(tries) > 0:
            return tries[0]
    
    # if we reached this point, we didn't find anything. return the exact
    # path we tried first and let upstream report file not found.
    return f"{where}/{hostname}"


def main():
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    parser.add_argument("--first-boot", nargs=1, metavar="HOSTNAME")
    parser.add_argument("--zcripts-path", nargs=1, default=DEFAULT_ZCRIPTS_PATH)
    ns = parser.parse_args()

    if ns.first_boot:
        script_path = find_script(ns.zcripts_path, ns.first_boot[0])
        try:
            os.execl(script_path, script_path)
        except OSError as e:
            raise parser.error(f"{script_path}: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
