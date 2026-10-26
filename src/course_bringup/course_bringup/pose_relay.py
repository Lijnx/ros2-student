"""Republish turtlesim poses unchanged with best-effort reliability."""

from course_bringup.qos import pose_qos
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose


class PoseRelay(Node):
    """Keep both topic names relative so launch owns the wiring."""

    def __init__(self, **kwargs):
        super().__init__('pose_relay', **kwargs)
        self.publisher = self.create_publisher(Pose, 'sensor_pose', pose_qos())
        self.subscription = self.create_subscription(
            Pose, 'pose', self.publisher.publish, 10)
        self.get_logger().info('pose -> sensor_pose: best_effort, volatile, depth=10')


def main(args=None):
    """Run the relay until shutdown and release its resources."""
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
