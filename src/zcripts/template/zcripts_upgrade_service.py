"""
Embedding the zcripts-upgrade service unit as a string constant.

Nuitka (non-commercial) does not permit files to be embedded in such a way as to
be usable by importlib.resources, so this is our compromise.
"""

from inspect import cleandoc


ZCRIPTS_UPGRADE_SERVICE = cleandoc(
    """
    [Unit]
    Description=zcripts self-upgrade service
    Before=systemd-user-sessions.service
    RequiresMountsFor={vars[mount_point]}
    Wants=network-online.target
    After=network-online.target
    ConditionPathExists=%E/zcripts/answers.toml

    [Service]
    Type=oneshot
    ExecStart=zcripts upgrade --answers-file=%E/zcripts/answers.toml
    RemainAfterExit=yes

    [Install]
    WantedBy=multi-user.target
    """
) + "\n"
