"""Exercise installed launch, absolute namespace spelling and clean shutdown."""

import os
from pathlib import Path
import signal
import subprocess
import time

from ament_index_python.packages import get_package_share_directory
import rclpy
from rclpy.node import Node
from rclpy.qos import ReliabilityPolicy
from turtlesim_msgs.msg import Pose
import yaml


def test_installed_launch_and_namespace(tmp_path):
    env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
    bag = tmp_path / 'bag'
    log_path = tmp_path / 'launch.log'
    rclpy.init()
    observer = Node('launch_test_observer')
    poses = []
    observer.create_subscription(Pose, '/robot_b/sensor_pose', poses.append,
                                 rclpy.qos.qos_profile_sensor_data)
    with log_path.open('w') as log:
        child = subprocess.Popen(
            ['ros2', 'launch', 'course_bringup', 'patrol.launch.py',
             'namespace:=/robot_b', 'record:=true', f'bag_dir:={bag}'],
            env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                rclpy.spin_once(observer, timeout_sec=0.1)
                readers = observer.get_subscriptions_info_by_topic('/robot_b/sensor_pose')
                reader_names = {endpoint.node_name for endpoint in readers}
                if poses and {'pose_subscriber', 'rosbag2_recorder'} <= reader_names:
                    break
                assert child.poll() is None, log_path.read_text()
            else:
                raise AssertionError('No namespaced sensor stream: ' + log_path.read_text())
            names = observer.get_node_names_and_namespaces()
            assert ('patrol', '/robot_b') in names
            assert ('turtlesim', '/') in names
            assert not observer.get_publishers_info_by_topic('/robot_a/sensor_pose')
            command = observer.get_publishers_info_by_topic('/turtle1/cmd_vel')
            assert len(command) == 1
            assert command[0].node_namespace == '/robot_b'
            for endpoint in readers:
                assert endpoint.qos_profile.reliability == ReliabilityPolicy.BEST_EFFORT
            time.sleep(1)
        finally:
            if child.poll() is None:
                child.send_signal(signal.SIGINT)
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                    raise AssertionError('Launch did not stop: ' + log_path.read_text())
            observer.destroy_node()
            rclpy.try_shutdown()
    assert child.returncode == 0, log_path.read_text()
    assert 'process has died' not in log_path.read_text()
    info = yaml.safe_load((bag / 'metadata.yaml').read_text())['rosbag2_bagfile_information']
    assert info['storage_identifier'] == 'mcap'
    topics = info['topics_with_message_count']
    assert len(topics) == 1
    assert topics[0]['topic_metadata']['name'] == '/robot_b/sensor_pose'
    assert topics[0]['message_count'] > 0
    installed = Path(get_package_share_directory('course_bringup')) / 'config'
    profile = yaml.safe_load((installed / 'qos-overrides.yaml').read_text())
    source = Path(__file__).resolve().parents[3] / 'config' / 'qos-overrides.yaml'
    assert profile == yaml.safe_load(source.read_text())
    assert profile['/robot_a/sensor_pose']['depth'] == 10
