#!/bin/bash
set -xue

# QEMU file path
QEMU=qemu-system-riscv32

# Start QEMU
# -machine virt: Start a virt machine. 
# -bios default: Use the default firmware (OpenSBI in this case)
# -nographic: Start QEMU without a GUI window
# -serial mon:stdio: Connect QEMU's standard input/ouput to the virtual machine's serial port. Sepcifying mon: allows switching to the QEMU monitor by pressing 
# Ctrl + A then C.
# --no-reboot: If the virtual machine crashes, stop the emulator without rebooting (useful for debugging)
$QEMU -machine virt -bios default -nographic -serial mon:stdio --no-reboot
