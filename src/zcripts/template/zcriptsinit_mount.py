"""
Embedding the mount unit as a string constant.

Nuitka (non-commercial) does not permit files to be embedded in such a way as to
be usable by importlib.resources, so this is our compromise.
"""

from inspect import cleandoc


ZCRIPTSINIT_MOUNT = cleandoc(
    """
    [Unit]
    Description=zcriptsinit share
    DefaultDependencies=no
    Wants=network-online.target
    After=network-online.target

    [Mount]
    What={vars[fileshare]}
    Where={vars[mount_point]}
    Type=cifs
    Options=defaults,guest,noserverino,nofail
    TimeoutSec=30

    [Install]
    WantedBy=multi-user.target
    """
) + "\n"
