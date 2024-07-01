"""
Set some booleans that control runtime options.
"""

SELF_UPGRADE = False        # controls whether 'zcripts upgrade' is available
INSTALL_SYSTEMD = False     # controls whether 'zcripts generate-systemd' has 
                            # options to install in the root filesystem.
                            # --unit-file-path, --config-path, and --internal-use-install-silent
