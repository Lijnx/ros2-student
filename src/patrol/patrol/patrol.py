"""Subscribe to turtle pose and publish a parameterized velocity command."""

from dataclasses import replace

from geometry_msgs.msg import Twist
from patrol.control import command_for_pose, PatrolSettings, validate_settings
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.parameter import Parameter
from turtlesim_msgs.msg import Pose


class Patrol(Node):
    """Publish configured motion after receiving the first pose."""

    def __init__(self) -> None:
        super().__init__('patrol')
        self.latest_pose: Pose | None = None
        self.pose_subscription = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10)
        self.command_publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.declare_parameter('linear_speed', 0.5)
        self.declare_parameter('turn_rate', 0.3)
        self.declare_parameter('publish_hz', 10.0)
        self.settings = PatrolSettings(
            self.get_parameter('linear_speed').value,
            self.get_parameter('turn_rate').value,
            self.get_parameter('publish_hz').value)
        reason = validate_settings(self.settings)
        if reason is not None:
            raise ValueError(reason)
        self.command_timer = self.create_timer(
            1.0 / self.settings.publish_hz, self.on_timer)
        self.add_on_set_parameters_callback(self.validate_parameters)
        self.add_post_set_parameters_callback(self.apply_parameters)

    def proposed_settings(self, parameters: list[Parameter]) -> PatrolSettings:
        """Combine a parameter update with the current active settings."""
        values = {
            parameter.name: parameter.value for parameter in parameters
            if parameter.name in ('linear_speed', 'turn_rate', 'publish_hz')
        }
        return replace(self.settings, **values)

    def validate_parameters(
            self, parameters: list[Parameter]) -> SetParametersResult:
        """Reject invalid values before changing the active state or timer."""
        reason = validate_settings(self.proposed_settings(parameters))
        return SetParametersResult(successful=reason is None, reason=reason or '')

    def apply_parameters(self, parameters: list[Parameter]) -> None:
        """Apply accepted values, replacing rather than duplicating a timer."""
        proposed = self.proposed_settings(parameters)
        if proposed.publish_hz != self.settings.publish_hz:
            self.command_timer.cancel()
            self.destroy_timer(self.command_timer)
            self.command_timer = self.create_timer(
                1.0 / proposed.publish_hz, self.on_timer)
        self.settings = proposed

    def on_pose(self, message: Pose) -> None:
        """Keep the newest pose for the next timer callback."""
        self.latest_pose = message

    def on_timer(self) -> None:
        """Publish one Twist using the last available pose."""
        linear_x, angular_z = command_for_pose(
            self.latest_pose, self.settings.linear_speed, self.settings.turn_rate)
        command = Twist()
        command.linear.x = linear_x
        command.angular.z = angular_z
        self.command_publisher.publish(command)


def main(args=None):
    """Run callbacks until interrupted, then release ROS resources."""
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
