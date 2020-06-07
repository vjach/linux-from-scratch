import sys
import sh
from sh import wget, tar, make, git, chown, dd, mkdir, sfdisk, losetup, partx, cat, sync, mount, mkimage, cp, rsync, touch, apt
from pathlib import Path
from sysbuilder import Bootloader, Kernel, RootFS, check_files
# bison device-tree-compiler gcc-arm-linux-gnueabihf flex swig u-boot-tools

mkfsvfat = sh.Command('mkfs.vfat')
mkfsext4 = sh.Command('mkfs.ext4')

def LicheePiZero_Bootloader(workdir):
    bootloader = Bootloader('/tmp/test/')
    bootloader.fetch("https://github.com/u-boot/u-boot/archive/v2020.07-rc3.tar.gz")
    # TODO: change config
    bootloader.build('arm', 'arm-linux-gnueabihf-', 'LicheePi_Zero_defconfig')

    expected_files = {
            'bootstrap': 'u-boot-sunxi-with-spl.bin',
            'bin':'u-boot.bin',
            }

    expected_files = {desc: str(Path(bootloader._dir).joinpath(f)) for desc, f in expected_files.items()}
    missing_files = check_files(expected_files.values())
    if len(missing_files):
        print('Files missing:\n {}'.format(missing_files))
        return None

    return expected_files


def LicheePiZero_Kernel(workdir):
    ARCH = 'arm'
    kernel = Kernel(workdir)
    kernel.fetch("https://github.com/torvalds/linux/archive/v5.7.tar.gz")
    # TODO: change config
    kernel.build(ARCH, 'arm-linux-gnueabihf-', 'sunxi_defconfig')

    expected_files = {
            'bin': 'zImage',
            'dtb': 'dts/sun8i-v3s-licheepi-zero.dtb',
            }

    expected_files = {k: str(Path(kernel._dir).joinpath('arch/{}/boot/'.format(ARCH),f)) for k, f in expected_files.items()}
    missing_files = check_files(expected_files.values())
    if len(missing_files):
        print('Files missing:\n {}'.format(missing_files))
        return None

    return expected_files


def LicheePiZero_RootFS(workdir):
    ARCH = 'arm'
    rootfs = RootFS(workdir)
    rootfs.fetch('')
    # TODO: change config
    rootfs.build(ARCH, 'arm-linux-gnueabihf-', 'resources/busybox_config')

    expected_files = {
            'rootdir': '_install'
            }

    expected_files = {desc: str(Path(rootfs._dir).joinpath(f)) for desc, f in expected_files.items()}
    missing_files = check_files(expected_files.values())
    if len(missing_files):
        print('Files missing:\n {}'.format(missing_files))
        return None

    return expected_files


def LicheePiImage(workdir, boot_files, kernel_files, rootfs_files):
    mkdir('-p', workdir)
    IMAGE_NAME = 'sdcard.img'
    IMAGE_PATH = str(Path(workdir).joinpath(IMAGE_NAME))

    dd('if=/dev/zero', 'of={}'.format(IMAGE_PATH), 'bs=1M', 'count=300')

    loop_dev = str(losetup('-f')).split()[0]
    losetup(loop_dev, IMAGE_PATH)
    sfdisk(cat(_in='1M,16M,c\n,,L'), loop_dev)
    partx('-u', loop_dev)
    mkfsvfat('{}p1'.format(loop_dev))
    mkfsext4('{}p2'.format(loop_dev))
    dd('if=/dev/zero', 'of={}'.format(loop_dev), 'bs=1K', 'seek=1', 'count=1023')
    dd('if={}'.format(boot_files['bootstrap']), 'of={}'.format(loop_dev), 'bs=1K', 'seek=8');
    sync()
    mkdir('-p', '/tmp/p1')
    mkdir('-p', '/tmp/p2')
    mount('{}p1'.format(loop_dev), '/tmp/p1')
    mount('{}p2'.format(loop_dev), '/tmp/p2')
    cp(boot_files['bin'], '/tmp/p1/');
    cp(kernel_files['bin'], '/tmp/p1/');
    cp(kernel_files['dtb'], '/tmp/p1/');
    mkimage('-C', 'none', '-A', 'arm', '-T', 'script', '-d', './resources/boot.cmd', '/tmp/p1/boot.scr')

    rsync('-r', '--links', rootfs_files['rootdir'] + '/', '/tmp/p2/')
    mkdir('-p', '/tmp/p2/etc/init.d')
    mkdir('-p', '/tmp/p2/proc')
    mkdir('-p', '/tmp/p2/dev')
    mkdir('-p', '/tmp/p2/sys')
    mkdir('-p', '/tmp/p2/var')
    touch('/tmp/p2/etc/init.d/rcS')
    chown('-R', 'root:root', '/tmp/p2/')
    

def install_dependencies():
    dependencies = [
            'bison',
            'device-tree-compiler',
            'gcc-arm-linux-gnueabihf',
            'flex',
            'swig',
            'u-boot-tools',
            ]

    apt('install', *dependencies)


if __name__ == '__main__':
    boot_files = LicheePiZero_Bootloader('/tmp/test')
    kernel_files = LicheePiZero_Kernel('/tmp/test')
    rootfs_files = LicheePiZero_RootFS('/tmp/test')

    LicheePiImage('/tmp/test/image', boot_files, kernel_files, rootfs_files)


