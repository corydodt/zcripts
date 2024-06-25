"""
Embedding the service unit as a string constant.

Nuitka (non-commercial) does not permit files to be embedded in such a way as to
be usable by importlib.resources, so this is our compromise.
"""
from inspect import cleandoc


ZCRIPTS_SERVICE=cleandoc("""
    [Unit]
    Description=zcripts vm bootstrapper
    Before=systemd-user-sessions.service
    RequiresMountsFor={vars[mount_point]}
    Wants=network-online.target
    After=network-online.target
    ConditionPathExists=!%S/%N-first-boot.done

    [Service]
    Type=oneshot
    ExecStart=zcripts boot --ignore-missing-host
    ExecStartPost=touch %S/%N-first-boot.done
    RemainAfterExit=yes

    [Install]
    WantedBy=multi-user.target
    """)
