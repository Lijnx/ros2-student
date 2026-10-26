"""Count sensor poses using an explicitly selected reliability policy."""

from course_bringup.qos import pose_qos
from rcl_interfaces.msg import ParameterDescriptor
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


class PoseSubscriber(Node):
    """Log zero as well as nonzero counts to make missing delivery visible."""

    def __init__(self, **kwargs):
        super().__init__('pose_subscriber', **kwargs)
        self.declare_parameter(
            'reliability', 'best_effort',
            ParameterDescriptor(read_only=True))
        self.reliability = self.get_parameter('reliability').value
        self.received = 0
        self.latest_pose = None
        self.subscription = self.create_subscription(
            Pose, 'sensor_pose', self.on_pose, pose_qos(self.reliability))
        self.timer = self.create_timer(1.0, self.log_count)
        self.get_logger().info(f'sensor_pose reliability={self.reliability}')

    def on_pose(self, message: Pose):
        """Retain the last message and count successful deliveries."""
        self.latest_pose = message
        self.received += 1

    def log_count(self):
        """Report delivery without adding another recorded topic."""
        self.get_logger().info(
            f'reliability={self.reliability} received={self.received}')


def main(args=None):
    """Run the reader until shutdown and release its resources."""
    rclpy.init(args=args)
    node = PoseSubscriber()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
