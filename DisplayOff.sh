#!/bin/bash

# Function to restore terminal settings and wake monitors
cleanup() {
    if [ -n "$OLD_STTY" ]; then
        stty "$OLD_STTY" 2>/dev/null || true
    fi
    xset dpms force on 2>/dev/null || true
}

# Save current terminal settings
OLD_STTY=$(stty -g 2>/dev/null || true)

# Ensure cleanup runs on script exit
trap cleanup EXIT INT TERM

# Turn off the monitors
echo "Turning off monitors. Press SPACE to wake."
sleep 0.5
xset dpms force off 2>/dev/null || true

# Wait for SPACE key using a simple blocking read with a long timeout
# This avoids TTY complexity by just reading from stdin
read -n 1 -s -t 300 key || true

# Restore immediately
stty "$OLD_STTY" 2>/dev/null || true
xset dpms force on 2>/dev/null || true
sleep 0.5

echo
echo "Monitor restored."

# Done - exit and let trap clean up
exit 0
