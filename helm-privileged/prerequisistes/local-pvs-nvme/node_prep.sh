mkdir -p /var/lib/quobyte/devices/registry-state
mkdir /var/lib/quobyte/devices/data1
mkdir /var/lib/quobyte/devices/metadata1
mkfs.xfs /dev/nvme0n1
mkfs.xfs /dev/nvme0n2
mount /dev/nvme0n1 /var/lib/quobyte/devices/metadata1/
mount /dev/nvme0n2 /var/lib/quobyte/devices/data1/

