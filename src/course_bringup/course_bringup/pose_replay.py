"""Display recorded poses in turtlesim without issuing velocity commands."""

from course_bringup.qos import pose_qos
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim_msgs.msg import Pose
from turtlesim_msgs.srv import TeleportAbsolute


class PoseReplay(Node):
    """Keep only the latest pose while a teleport service request is pending."""

    def __init__(self, **kwargs):
        super().__init__('pose_replay', **kwargs)
        self.pending_pose = None
        self.request = None
        self.client = self.create_client(TeleportAbsolute, 'turtle1/teleport_absolute')
        self.subscription = self.create_subscription(
            Pose, 'sensor_pose', self.on_pose, pose_qos())
        self.timer = self.create_timer(0.02, self.teleport)
        self.get_logger().info(
            'sensor_pose -> turtle1/teleport_absolute; waiting for poses and service')

    def on_pose(self, message: Pose):
        """Replace any stale pose instead of building up a service queue."""
        self.pending_pose = message

    def teleport(self):
        """Send at most one asynchronous service request at a time."""
        if self.request is not None:
            if not self.request.done():
                return
            try:
                self.request.result()
            except Exception as error:
                self.get_logger().error(f'Teleport failed: {error}')
            self.request = None
        if self.pending_pose is None or not self.client.service_is_ready():
            return
        pose = self.pending_pose
        self.pending_pose = None
        self.request = self.client.call_async(
            TeleportAbsolute.Request(x=pose.x, y=pose.y, theta=pose.theta))


def main(args=None):
    """Run the visual replay adapter until shutdown."""
    rclpy.init(args=args)
    node = PoseReplay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
