"""Tests for command selection without starting a ROS graph."""

from dataclasses import replace
import math
from types import SimpleNamespace

from patrol.control import command_for_pose, PatrolSettings, validate_settings


def test_no_pose_stops_turtle():
    assert command_for_pose(None) == (0.0, 0.0)


def test_received_pose_enables_motion():
    pose = SimpleNamespace(x=5.0, y=5.0, theta=0.0)
    assert command_for_pose(pose) == (0.5, 0.3)
    assert command_for_pose(pose, 0.8, -0.2) == (0.8, -0.2)


def test_ten_to_five_hertz_is_valid():
    current = PatrolSettings()
    assert validate_settings(current) is None
    assert validate_settings(replace(current, publish_hz=5.0)) is None


def test_invalid_frequency_is_rejected():
    current = PatrolSettings()
    for value in (0.0, -1.0, math.nan, math.inf):
        assert validate_settings(replace(current, publish_hz=value)) is not None


def test_motion_ranges_and_types_are_checked():
    current = PatrolSettings()
    assert validate_settings(replace(current, linear_speed=0.0)) is None
    assert validate_settings(replace(current, linear_speed=1.0)) is None
    assert validate_settings(replace(current, turn_rate=-1.0)) is None
    assert validate_settings(replace(current, turn_rate=1.0)) is None
    for settings in (
            replace(current, linear_speed=-0.1),
            replace(current, linear_speed=1.1),
            replace(current, turn_rate=-1.1),
            replace(current, turn_rate=1.1),
            replace(current, linear_speed=math.nan),
            replace(current, turn_rate=math.inf),
            replace(current, publish_hz=True),
    ):
        assert validate_settings(settings) is not None
