"""Launch one global turtle and a namespaced patrol/QoS demonstration."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """Resolve substitutions at launch time, including the recorder condition."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    reliability = LaunchConfiguration('subscriber_reliability')
    return LaunchDescription([
        DeclareLaunchArgument('namespace', default_value='robot_a'),
        DeclareLaunchArgument('record', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('bag_dir', default_value='evidence/pr05/bag'),
        DeclareLaunchArgument(
            'subscriber_reliability', default_value='reliable',
            choices=['reliable', 'best_effort']),
        LogInfo(msg=['namespace=', namespace, ', record=', record,
                     ', subscriber_reliability=', reliability, ', bag_dir=', bag_dir]),
        Node(package='turtlesim', executable='turtlesim_node', namespace='/',
             output='screen'),
        Node(package='patrol', executable='patrol', namespace=namespace,
             remappings=[('turtle1/pose', '/turtle1/pose'),
                         ('cmd_vel', '/turtle1/cmd_vel')], output='screen'),
        Node(package='course_bringup', executable='pose_relay', namespace=namespace,
             remappings=[('pose', '/turtle1/pose')], output='screen'),
        Node(package='course_bringup', executable='pose_subscriber', namespace=namespace,
             parameters=[{'reliability': reliability}], output='screen'),
        ExecuteProcess(
            cmd=['ros2', 'bag', 'record', '-s', 'mcap', '-o', bag_dir,
                 '--disable-keyboard-controls',
                 '--qos-profile-overrides-path', PathJoinSubstitution([
                     FindPackageShare('course_bringup'), 'config', 'qos-overrides.yaml']),
                 '--topics', PathJoinSubstitution(['/', namespace, 'sensor_pose'])],
            condition=IfCondition(record), output='screen'),
    ])
