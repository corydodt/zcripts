"""
Set some booleans that control runtime options.
"""

# controls whether 'zcripts upgrade' is available
SELF_UPGRADE = False

# controls whether 'zcripts generate-systemd' has options to install in the root
# filesystem.
# --unit-file-path, --config-path, and --internal-use-install-silent
INSTALL_SYSTEMD = False
