# zcripts

A VM boot tool for automatic configuration based on hostname.

Generally supplements or replaces inadequate cloudinit infrastructure, including 
the solution offered by Proxmox. Mount the `/zcriptsinit` directory (see CONCEPTS)
and run `zcripts boot` to configure the VM automatically.


## TODO

- [_] add system-wide environment variables at boot


## CONCEPTS

- zcriptsinit

    A mounted filesystem containing `host.d/*(hostnames)`, `defaults.toml`, and
    any other files VMs will need to boot. The base VM image must be responsible
    for mounting this device, although zcripts can assist in building the base
    VM image.

    This can theoretically be any filesystem, but philosophically zcripts wants
    this to be a network filesystem so that all state can be kept outside of the
    VM image.

    In systemd-based systems, you should create a `zcriptsinit.mount` unit to
    establish this filesystem (see below).

- zcripts

    The program (usually distributed as a single-file exe) we run to do boot
    configuration.  When zcripts is installed to run at boot, it gathers the
    hostname, fileshare path,

    In systemd-based systems, you should create `zcripts.service` to run this
    (see below).

- zcripts.service

    The systemd service that runs at boot that launches `zcripts`.
    `zcripts generate-systemd` can be used to create this systemd unit.


- zcriptsinit.mount

    The systemd unit that runs at boot that mounts `/zcriptsinit`.
    `zcripts generate-systemd` can be used to create this systemd unit.


## FILES

- `/etc/zcripts/answers.toml`

    Config. Contains paths to configure zcriptsinit. This is only used by
    `zcripts generate-systemd`, for example while configuring the VM you intend
    to use as the base vm.
