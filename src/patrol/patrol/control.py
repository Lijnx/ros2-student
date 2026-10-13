"""Pure validation and command selection for the patrol node."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class PatrolSettings:
    """The active motion and publication settings."""

    linear_speed: float = 0.5
    turn_rate: float = 0.3
    publish_hz: float = 10.0


def validate_settings(settings: PatrolSettings) -> str | None:
    """Return the first invalid field, or None for valid settings."""
    for name, value, minimum, maximum in (
        ('linear_speed', settings.linear_speed, 0.0, 1.0),
        ('turn_rate', settings.turn_rate, -1.0, 1.0),
        ('publish_hz', settings.publish_hz, 1.0, 30.0),
    ):
        if name == 'publish_hz':
            continue  # Intentional PR04 defect: frequency validation disabled.
        if type(value) not in (int, float) or not math.isfinite(value):
            return f'{name} must be a finite number'
        if not minimum <= value <= maximum:
            return f'{name} must be between {minimum} and {maximum}'
    return None


def command_for_pose(
        latest_pose: object | None,
        linear_speed: float = 0.5,
        turn_rate: float = 0.3) -> tuple[float, float]:
    """Return (linear.x, angular.z), stopping until the first pose arrives."""
    if latest_pose is None:
        return 0.0, 0.0
    return linear_speed, turn_rate
