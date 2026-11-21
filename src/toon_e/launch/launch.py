"""
Full Loon-E bringup: ZED X, robot description, hardware node and Nav2.

TF tree (the ZED camera is the URDF root; this wrapper has no base_frame
parameter, so base_link hangs below the camera):

    map -(ZED)-> odom -(ZED)-> zedx_camera_link -(URDF)-> base_link -> props, gps_link
                                                 +-> zedx_camera_center -> optical frames

See src/toon_e/README.md for the full description.

Nav2's velocity_smoother publishes geometry_msgs/Twist on /cmd_vel, which
toon_e_hardware's hardware_node turns into propeller throttles.

Usage:
    ros2 launch toon_e launch.py              # everything
    ros2 launch toon_e launch.py nav:=false   # no Nav2, e.g. for teleop
    ros2 launch toon_e launch.py sim:=true    # no hardware_node
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    """Assemble the bringup."""
    camera_name = LaunchConfiguration('camera_name')
    camera_model = LaunchConfiguration('camera_model')
    zed_node_name = LaunchConfiguration('zed_node_name')
    use_sim_time = LaunchConfiguration('use_sim_time')
    sim = LaunchConfiguration('sim')
    nav = LaunchConfiguration('nav')
    enable_gnss = LaunchConfiguration('enable_gnss')

    toon_e_share = get_package_share_directory('toon_e')
    hardware_config = os.path.join(toon_e_share, 'config', 'config.yaml')
    nav2_params = os.path.join(toon_e_share, 'config', 'nav2_params.yaml')

    # Robot description lives in the le1000_urdf_t4 package (src/loone_urdf;
    # the directory name and the package name differ).
    xacro_path = os.path.join(
        get_package_share_directory('le1000_urdf_t4'), 'urdf', 'loone_asv.urdf.xacro')
    robot_description = {
        'robot_description': ParameterValue(
            Command([
                'xacro ', xacro_path,
                ' camera_name:=', camera_name,
                ' camera_model:=', camera_model,
            ]),
            value_type=str)
    }

    zed_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(toon_e_share, 'launch', 'zed_launch.py')),
        launch_arguments={
            'camera_name': camera_name,
            'camera_model': camera_model,
            'zed_node_name': zed_node_name,
            'use_sim_time': use_sim_time,
            'enable_gnss': enable_gnss,
        }.items())

    # Publishes the ZED's own frames (via zed_macro.urdf.xacro), the
    # cam_1_to_base_link joint that hangs base_link below the camera, and the
    # boat's fixed frames. The only publisher of <camera>_camera_link -> base_link.
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='log',
        parameters=[robot_description, {'use_sim_time': use_sim_time}],
    )

    # The name= value must match the top-level key in config.yaml
    # (/hardware_node) for its parameters to apply.
    hardware_node = Node(
        package='toon_e_hardware',
        executable='hardware_node',
        name='hardware_node',
        output='screen',
        parameters=[hardware_config, {'use_sim_time': use_sim_time}],
        condition=UnlessCondition(sim),
    )

    # Humble's navigation_launch.py starts the controller, planner, smoother,
    # behavior, bt_navigator, waypoint_follower and velocity_smoother servers,
    # and remaps the velocity_smoother output to /cmd_vel. No map_server/amcl:
    # the ZED provides map -> odom.
    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('nav2_bringup'),
                'launch',
                'navigation_launch.py')),
        launch_arguments={
            'params_file': nav2_params,
            'use_sim_time': use_sim_time,
            'autostart': 'true',
        }.items(),
        condition=IfCondition(nav),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_name', default_value='zedx',
            description='ZED camera name / namespace (sets the <name>_camera_link frame).'),
        DeclareLaunchArgument(
            'camera_model', default_value='zedx',
            description='ZED camera model passed to the wrapper.'),
        DeclareLaunchArgument(
            'zed_node_name', default_value='zed_node',
            description='ZED wrapper node name inside the camera namespace.'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock simulated time. Keep false on the real boat.'),
        DeclareLaunchArgument(
            'sim', default_value='false',
            description='Simulation mode: skip hardware_node (Isaac Sim drives the actuators).'),
        DeclareLaunchArgument(
            'nav', default_value='true',
            description='Start Nav2. Set false when driving with teleop, so only one '
                        'node publishes /cmd_vel.'),
        DeclareLaunchArgument(
            'enable_gnss', default_value='false',
            description='Fuse /navsatfix into the ZED pose. Needs a GPS publisher.'),
        hardware_node,
        zed_launch,
        robot_state_publisher,
        nav2_launch,
    ])
