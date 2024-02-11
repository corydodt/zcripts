"""
zcripts
"""

import argparse
import sys

from proxmoxer import ProxmoxAPI


PROXMOX_ENDPOINT = "pve.carrotwithchickenlegs.com"
USER = "aaaa@pam"

def main():
    parser = argparse.ArgumentParser()
    parser.description = __doc__
    parser.formatter_class = argparse.RawDescriptionHelpFormatter
    ns = parser.parse_args()

    pmapi = ProxmoxAPI(PROXMOX_ENDPOINT, user=USER, token_name=xxxx, token_value=yyyy)
    print("auth")
    print(pmapi.nodes.get())

    return 0

if __name__ == "__main__":
    sys.exit(main())
