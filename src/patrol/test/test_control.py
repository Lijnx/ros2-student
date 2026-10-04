"""Tests for command selection without starting a ROS graph."""

from types import SimpleNamespace

from patrol.control import command_for_pose


def test_no_pose_stops_turtle():
    assert command_for_pose(None) == (0.0, 0.0)


def test_received_pose_enables_motion():
    pose = SimpleNamespace(x=5.0, y=5.0, theta=0.0)
    assert command_for_pose(pose) == (0.5, 0.3)
