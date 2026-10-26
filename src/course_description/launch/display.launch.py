"""Expand the installed Xacro and display its fixed frames in RViz."""

from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Use robot_state_publisher as the sole owner of model transforms."""
    share = FindPackageShare('course_description')
    model = PathJoinSubstitution([share, 'urdf', 'vehicle.urdf.xacro'])
    config = PathJoinSubstitution([share, 'rviz', 'vehicle.rviz'])
    return LaunchDescription([
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            parameters=[{'robot_description': ParameterValue(
                Command(['xacro ', model]), value_type=str)}], output='screen'),
        Node(package='rviz2', executable='rviz2', arguments=['-d', config],
             output='screen'),
    ])
