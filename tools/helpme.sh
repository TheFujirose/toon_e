#!/bin/bash
mtu && reset_cam && sudo service driver_zed_loader start && sleep 15 && ros2 launch toon_e launch.py
