"""
Embedding the service unit as a string constant.

Nuitka (non-commercial) does not permit files to be embedded in such a way as to
be usable by importlib.resources, so this is our compromise.
"""

from inspect import cleandoc


ZCRIPTS_UPGRADE_TIMER = (
    cleandoc(
        """
    [Unit]
    Description=check for zcripts upgrade daily
    Requires=zcripts-upgrade.service

    [Timer]
    OnCalendar=*-*-* 04:12:00

    [Install]
    WantedBy=timers.target
    """
    )
    + "\n"
)
