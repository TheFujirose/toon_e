#!/bin/bash
# This reinstalls the driver. should have confirmation.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WS_ROOT="$(dirname "$SCRIPT_DIR")"

 sudo apt install ./zed.deb -y && sudo systemctl start driver_zed_loader.service && sudo systemctl start zed_x_daemon.service && sudo systemctl start IMU_Daemon.service && sudo systemctl restart nvargus-daemon.service && cd "$WS_ROOT" && source install/setup.sh && ros2 launch toon_e launch.py
