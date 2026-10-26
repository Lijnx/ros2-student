"""Explicit QoS profiles shared by the relay and its reader."""

from rclpy.qos import DurabilityPolicy, HistoryPolicy, LivelinessPolicy
from rclpy.qos import QoSProfile, ReliabilityPolicy


def pose_qos(reliability: str = 'best_effort') -> QoSProfile:
    """Reject misspellings rather than silently choosing a different profile."""
    policies = {
        'best_effort': ReliabilityPolicy.BEST_EFFORT,
        'reliable': ReliabilityPolicy.RELIABLE,
    }
    if reliability not in policies:
        raise ValueError('reliability must be reliable or best_effort')
    return QoSProfile(
        history=HistoryPolicy.KEEP_LAST, depth=10,
        reliability=policies[reliability], durability=DurabilityPolicy.VOLATILE,
        liveliness=LivelinessPolicy.AUTOMATIC)
