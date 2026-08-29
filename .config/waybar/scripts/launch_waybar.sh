#!/usr/bin/env bash
# Kill any existing waybar or launch_waybar processes
pkill -x waybar 2>/dev/null
pkill -f launch_waybar.py 2>/dev/null
sleep 0.2

# Launch the proxy bridge daemon
python3 /home/kunal/.config/waybar/scripts/launch_waybar.py --daemon "$@"
