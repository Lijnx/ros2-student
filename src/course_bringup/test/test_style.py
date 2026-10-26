"""Apply the same Python style checks as the existing packages."""

from ament_flake8.main import main_with_errors
from ament_pep257.main import main as pep257_main


def test_flake8():
    result, errors = main_with_errors(argv=[])
    assert result == 0, '\n'.join(errors)


def test_pep257():
    assert pep257_main(argv=[]) == 0
