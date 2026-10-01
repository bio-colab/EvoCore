#!/bin/sh
# /opt/bootlocal.sh — Tiny Core Linux boot local execution hook
chmod +x /opt/evocore/evocore_init.sh 2>/dev/null
/opt/evocore/evocore_init.sh &
