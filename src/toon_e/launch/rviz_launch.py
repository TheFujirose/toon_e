"""
Open RViz2 with Nav2's default view.

nav2_default_view.rviz shows the costmaps, planned paths and the robot
footprint, and has the "2D Goal Pose" tool for sending NavigateToPose goals.
Run launch.py first (on the boat); this only opens the viewer.

Usage:
    ros2 launch toon_e rviz_launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Start rviz2 with the Nav2 config."""
    rviz_config = os.path.join(
        get_package_share_directory('nav2_bringup'), 'rviz', 'nav2_default_view.rviz')

    return LaunchDescription([
        Node(
            package='rviz2',
            executable='rviz2',
            name='toon_e_rviz2',
            output='screen',
            arguments=['-d', rviz_config],
        ),
    ])
