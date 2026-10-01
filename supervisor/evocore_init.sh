#!/bin/sh
# evocore_init.sh — Hook invoked by Tiny Core bootlocal.sh during system initialization
# Starts the EvoCore Autonomous Supervisor

export PATH="/usr/local/bin:/usr/bin:/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="/opt/evocore:/opt/evocore/src:$PYTHONPATH"

export PYTHONUNBUFFERED=1

# Run ldconfig to ensure all libraries in /usr/local/lib are cached
/sbin/ldconfig 2>/dev/null

log_output() {
    for tty in /dev/tty1 /dev/ttyS0; do
        if [ -c "$tty" ]; then
            echo "$@" > "$tty" 2>/dev/null
        fi
    done
}

# Display ASCII banner on detected consoles
if [ -f /opt/evocore/banner.txt ]; then
    for tty in /dev/tty1 /dev/ttyS0; do
        if [ -c "$tty" ]; then
            cat /opt/evocore/banner.txt > "$tty" 2>/dev/null
        fi
    done
fi

log_output "==========================================================================="
log_output "  Appliance Version : EvoCore v0.2.0 (Autonomous Laboratory Edition)"
log_output "  Kernel Release    : $(uname -r 2>/dev/null)"
log_output "  Machine Arch      : $(uname -m 2>/dev/null)"
log_output "  Total Memory      : $(grep MemTotal /proc/meminfo 2>/dev/null | awk '{print $2, $3}')"
log_output "==========================================================================="

if which python3 >/dev/null 2>&1; then
    PY_VER=$(python3 --version 2>&1)
    log_output "[*] Runtime Environment : $PY_VER detected."
    TARGET_TTY="/dev/tty1"
    if grep -q "console=ttyS0" /proc/cmdline; then
        TARGET_TTY="/dev/ttyS0"
    fi
    python3 -u /opt/evocore/supervisor.py > "$TARGET_TTY" 2>&1
else
    log_output "[!] Warning: Python 3 not detected in PATH."
    log_output "[*] Standalone Micro-Kernel mode active."
    log_output "[*] Darwin-Evolab environment is active."
fi
