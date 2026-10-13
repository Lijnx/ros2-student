"""Check that ROS parameter updates keep one valid active timer."""

from patrol.patrol import Patrol
import rclpy
from rclpy.parameter import Parameter


def test_parameter_updates_are_atomic():
    rclpy.init()
    node = Patrol()
    try:
        original_timer = node.command_timer
        assert len(list(node.timers)) == 1
        assert node.settings.publish_hz == 10.0

        result = node.set_parameters_atomically([
            Parameter('publish_hz', Parameter.Type.DOUBLE, 5.0)])
        assert result.successful
        assert node.settings.publish_hz == 5.0
        assert node.command_timer is not original_timer
        assert len(list(node.timers)) == 1
        assert node.get_parameter('publish_hz').value == 5.0

        active_timer = node.command_timer
        result = node.set_parameters_atomically([
            Parameter('linear_speed', Parameter.Type.DOUBLE, 0.8),
            Parameter('publish_hz', Parameter.Type.DOUBLE, 0.0)])
        assert not result.successful
        assert node.settings.linear_speed == 0.5
        assert node.settings.publish_hz == 5.0
        assert node.command_timer is active_timer
        assert len(list(node.timers)) == 1
        assert node.get_parameter('linear_speed').value == 0.5
        assert node.get_parameter('publish_hz').value == 5.0
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
