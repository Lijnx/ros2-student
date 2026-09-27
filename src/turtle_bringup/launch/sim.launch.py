"""Start the installed turtlesim executable."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """Launch one turtlesim node and show its output in the terminal."""
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            output='screen',
        ),
    ])
