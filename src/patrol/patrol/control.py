"""Pure command selection for the first pose-driven patrol node."""


def command_for_pose(latest_pose: object | None) -> tuple[float, float]:
    """Return (linear.x, angular.z), stopping until the first pose arrives."""
    if latest_pose is None:
        return 0.0, 0.0
    return 0.5, 0.3
