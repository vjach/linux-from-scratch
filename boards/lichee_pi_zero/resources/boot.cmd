setenv bootargs console=ttyS0,115200 earlyprintk rw root=/dev/mmcblk0p2 rootwait panic=10
load mmc 0:1 0x42000000 zImage
load mmc 0:1 0x41800000 sun8i-v3s-licheepi-zero.dtb
bootz 0x42000000 - 0x41800000
