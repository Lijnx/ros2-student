"""Subscribe to turtle pose and publish a simple velocity command."""

from geometry_msgs.msg import Twist
from patrol.control import command_for_pose
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


class Patrol(Node):
    """Publish a fixed motion command after receiving the first pose."""

    def __init__(self) -> None:
        super().__init__('patrol')
        self.latest_pose: Pose | None = None
        self.pose_subscription = self.create_subscription(
            Pose, '/turtle1/pose', self.on_pose, 10)
        self.command_publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.command_timer = self.create_timer(0.1, self.on_timer)

    def on_pose(self, message: Pose) -> None:
        """Keep the newest pose for the next timer callback."""
        self.latest_pose = message

    def on_timer(self) -> None:
        """Publish one Twist using the last available pose."""
        linear_x, angular_z = command_for_pose(self.latest_pose)
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
