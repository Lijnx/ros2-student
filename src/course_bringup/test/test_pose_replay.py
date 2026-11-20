"""Check the visual replay adapter using a real ROS service, without a GUI."""

import time

from course_bringup.pose_replay import PoseReplay
import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.task import Future
from turtlesim_msgs.msg import Pose
from turtlesim_msgs.srv import TeleportAbsolute


def test_pose_replay():
    rclpy.init()
    executor = SingleThreadedExecutor()
    adapter = PoseReplay(
        namespace='/pr05_replay_test',
        cli_args=['--ros-args', '-r', 'sensor_pose:=recorded_pose'])
    peer = Node('replay_peer', namespace='/pr05_replay_test')
    requests = []
    try:
        def on_teleport(request, response):
            requests.append((request.x, request.y, request.theta))
            return response

        service = peer.create_service(
            TeleportAbsolute, 'turtle1/teleport_absolute', on_teleport)
        publisher = peer.create_publisher(Pose, 'recorded_pose', 10)
        executor.add_node(adapter)
        executor.add_node(peer)

        # An outstanding service call must not accumulate more requests.
        pending = Future()
        adapter.request = pending
        adapter.on_pose(Pose(x=1.0, y=2.0, theta=0.1))
        latest = Pose(x=3.0, y=4.0, theta=0.2)
        adapter.on_pose(latest)
        adapter.teleport()
        assert adapter.request is pending
        assert adapter.pending_pose is latest
        pending.set_result(TeleportAbsolute.Response())

        # Exercise actual topic reception and service delivery.
        timer = peer.create_timer(0.05, lambda: publisher.publish(latest))
        end = time.monotonic() + 5.0
        while time.monotonic() < end:
            executor.spin_once(timeout_sec=0.05)
            if len(requests) >= 2:
                break
        assert timer is not None and service is not None
        assert len(requests) >= 2
        assert all(pose == pytest.approx((3.0, 4.0, 0.2)) for pose in requests)
        assert adapter.subscription.topic_name == '/pr05_replay_test/recorded_pose'
    finally:
        executor.shutdown()
        adapter.destroy_node()
        peer.destroy_node()
        rclpy.try_shutdown()
