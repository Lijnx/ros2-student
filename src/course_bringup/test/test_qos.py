"""Check QoS validation and delivery through the real relay."""

import time

from course_bringup.pose_relay import PoseRelay
from course_bringup.pose_subscriber import PoseSubscriber
from course_bringup.qos import pose_qos
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSCompatibility
from rclpy.qos import qos_check_compatible, ReliabilityPolicy
from rclpy.serialization import serialize_message
from turtlesim_msgs.msg import Pose


def test_profiles():
    profile = pose_qos()
    assert profile.reliability == ReliabilityPolicy.BEST_EFFORT
    assert profile.durability == DurabilityPolicy.VOLATILE
    assert profile.history == HistoryPolicy.KEEP_LAST
    assert profile.depth == 10
    assert pose_qos('reliable').reliability == ReliabilityPolicy.RELIABLE
    with pytest.raises(ValueError):
        pose_qos('relaiable')


@pytest.mark.parametrize('offered,requested,compatible', [
    ('best_effort', 'best_effort', True),
    ('best_effort', 'reliable', False),
    ('reliable', 'best_effort', True),
    ('reliable', 'reliable', True),
])
def test_reliability_matrix(offered, requested, compatible):
    compatibility, _ = qos_check_compatible(pose_qos(offered), pose_qos(requested))
    assert (compatibility == QoSCompatibility.OK) == compatible


def test_relay_delivery_and_incompatible_reader():
    rclpy.init()
    executor = SingleThreadedExecutor()
    nodes = []
    try:
        source = Node('source', namespace='/pr05_test')
        nodes.append(source)
        relay = PoseRelay(namespace='/pr05_test')
        nodes.append(relay)
        good = PoseSubscriber(
            namespace='/pr05_test', cli_args=['--ros-args', '-r', '__node:=good'])
        nodes.append(good)
        bad = PoseSubscriber(
            namespace='/pr05_test', cli_args=['--ros-args', '-r', '__node:=bad'],
            parameter_overrides=[Parameter('reliability', value='reliable')])
        nodes.append(bad)
        publisher = source.create_publisher(Pose, 'pose', 10)
        sample = Pose(x=1.25, y=2.5, theta=0.75, linear_velocity=0.5,
                      angular_velocity=0.3)
        timer = source.create_timer(0.02, lambda: publisher.publish(sample))
        for node in nodes:
            executor.add_node(node)
        end = time.monotonic() + 5.0
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.05)
        assert timer is not None
        assert good.received > 10
        assert serialize_message(good.latest_pose) == serialize_message(sample)
        assert bad.received == 0
        endpoints = source.get_publishers_info_by_topic('/pr05_test/sensor_pose')
        assert len(endpoints) == 1
        assert endpoints[0].qos_profile.reliability == ReliabilityPolicy.BEST_EFFORT
        assert len(source.get_subscriptions_info_by_topic('/pr05_test/sensor_pose')) == 2
        assert good.subscription.topic_name == '/pr05_test/sensor_pose'
    finally:
        executor.shutdown()
        for node in reversed(nodes):
            node.destroy_node()
        rclpy.try_shutdown()
