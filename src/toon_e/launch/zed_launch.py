"""
Start the ZED X wrapper configured as the localization source for Nav2.

The ZED owns both odometry transforms:

    map -(publish_map_tf)-> odom -(publish_tf)-> <camera_name>_camera_link

The robot description (camera frames + base_link) is published by launch.py's
robot_state_publisher from le1000_urdf_t4, so the wrapper's own URDF publisher
is turned off here. Running both would put two descriptions of the same camera
on /tf_static.

Usage:
    ros2 launch toon_e zed_launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    """Include zed_camera.launch.py with the toon_e overrides."""
    toon_e_share = get_package_share_directory('toon_e')

    custom_object_detection_config_path = os.path.join(
        toon_e_share, 'config', 'model.yaml')

    # custom_onnx_file in model.yaml is relative; the ZED SDK opens the path as
    # given, so pass the absolute installed path instead.
    model_onnx_path = os.path.join(toon_e_share, 'model', 'loone.onnx')

    # Launch-time parameter overrides, applied after every YAML file. Kept here
    # rather than in the zedx submodule's common_stereo.yaml so the fork stays
    # untouched.
    param_overrides = ';'.join([
        'object_detection.custom_onnx_file:=' + model_onnx_path,
        # With isaac_ros_nitros installed the wrapper publishes images through
        # NITROS only, which removes the image/compressed topics the basestation
        # camera feed uses over Wi-Fi.
        'debug.disable_nitros:=true',
        # On loop closure the wrapper otherwise resets odom -> camera_link to
        # identity. Nav2's local costmap and controller work in odom and need it
        # continuous; loop-closure corrections still land in map -> odom.
        'pos_tracking.reset_odom_with_loop_closure:=false',
        # Voxel-decimated cloud (~100 mm cells, ZED SDK >= 5.3) for the costmaps.
        # The full COMPACT cloud is ~9 MB per frame, too much to push through
        # DDS into two costmaps on the Jetson.
        'depth.voxel_point_cloud:=true',
    ])

    camera_name = LaunchConfiguration('camera_name')
    camera_model = LaunchConfiguration('camera_model')
    zed_node_name = LaunchConfiguration('zed_node_name')
    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_gnss = LaunchConfiguration('enable_gnss')

    zed_wrapper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('zed_wrapper'),
                'launch',
                'zed_camera.launch.py')),
        launch_arguments={
            'camera_name': camera_name,
            'camera_model': camera_model,
            'node_name': zed_node_name,
            'use_sim_time': use_sim_time,
            # launch.py's robot_state_publisher owns the description.
            'publish_urdf': 'false',
            'publish_tf': 'true',
            'publish_map_tf': 'true',
            # This launch argument overrides gnss_fusion.gnss_fusion_enabled in
            # common_stereo.yaml. Keep it false until something publishes
            # /navsatfix.
            'enable_gnss': enable_gnss,
            'custom_object_detection_config_path': custom_object_detection_config_path,
            'param_overrides': param_overrides,
        }.items())

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_name', default_value='zedx',
            description='ZED camera name; namespace and <name>_camera_link frame prefix.'),
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
            'enable_gnss', default_value='false',
            description='Fuse /navsatfix into the ZED pose. Needs a GPS publisher.'),
        zed_wrapper_launch,
    ])
