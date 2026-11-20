"""Check expanded URDF structure, expected geometry and model parameters."""

import math
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


MODEL = Path(__file__).resolve().parents[1] / 'urdf' / 'vehicle.urdf.xacro'


def expand(*args):
    """Test the actual Xacro executable rather than unexpanded XML."""
    return subprocess.check_output(['xacro', str(MODEL), *args], text=True)


def xyz(element):
    """Read a URDF origin with the standard zero default."""
    origin = element.find('origin')
    return tuple(float(x) for x in (
        origin.get('xyz', '0 0 0') if origin is not None else '0 0 0').split())


def test_urdf_tree(tmp_path):
    text = expand()
    model = ET.fromstring(text)
    links = [link.get('name') for link in model.findall('link')]
    joints = model.findall('joint')
    assert len(links) == len(set(links)) == 10
    assert len(joints) == len({joint.get('name') for joint in joints}) == 9
    parents = {}
    for joint in joints:
        parent = joint.find('parent').get('link')
        child = joint.find('child').get('link')
        assert parent in links and child in links and child not in parents
        parents[child] = parent
    assert set(links) - set(parents) == {'base_link'}
    for name in links:
        seen = set()
        while name in parents:
            assert name not in seen
            seen.add(name)
            name = parents[name]
        assert name == 'base_link'
    urdf = tmp_path / 'vehicle.urdf'
    urdf.write_text(text)
    subprocess.run(['check_urdf', str(urdf)], check=True)


def test_sensor_parents_and_offsets():
    model = ET.fromstring(expand())
    for name in ('camera', 'lidar', 'imu'):
        joint = model.find(f"joint[@name='{name}_joint']")
        assert joint.get('type') == 'fixed'
        assert joint.find('child').get('link') == f'{name}_link'
        assert joint.find('parent').get('link') == 'base_link', name
        assert xyz(joint) == pytest.approx((0.28, 0, 0.38))


@pytest.mark.parametrize('base,track,radius', [(0.8, 0.62, 0.12), (1.0, 0.7, 0.15)])
def test_wheel_geometry_and_parameters(base, track, radius):
    model = ET.fromstring(expand(
        f'wheel_base:={base}', f'track:={track}', f'wheel_radius:={radius}'))
    assert model.find("link[@name='base_link']/visual/geometry/box").get(
        'size') == '1.05 0.52 0.22'
    for side, sign in [('left', 1), ('right', -1)]:
        steering = model.find(f"joint[@name='front_{side}_steering_joint']")
        assert xyz(steering) == pytest.approx((base / 2, sign * track / 2, 0))
        assert steering.get('type') == 'revolute'
        assert steering.find('axis').get('xyz') == '0 0 1'
        rear = model.find(f"joint[@name='rear_{side}_wheel_joint']")
        assert xyz(rear) == pytest.approx((-base / 2, sign * track / 2, 0))
        front = model.find(f"joint[@name='front_{side}_wheel_joint']")
        assert xyz(front) == (0, 0, 0)
        assert front.find('parent').get('link') == f'front_{side}_knuckle'
        for end in ('front', 'rear'):
            joint = model.find(f"joint[@name='{end}_{side}_wheel_joint']")
            assert joint.get('type') == 'continuous'
            assert joint.find('axis').get('xyz') == '0 1 0'
            link = model.find(f"link[@name='{end}_{side}_wheel']")
            for tag in ('visual', 'collision'):
                cylinder = link.find(f'{tag}/geometry/cylinder')
                assert float(cylinder.get('radius')) == radius
                assert float(cylinder.get('length')) == 0.07
                rpy = link.find(f'{tag}/origin').get('rpy').split()
                assert tuple(map(float, rpy)) == pytest.approx((math.pi / 2, 0, 0))


def test_geometry_and_inertial_numbers():
    model = ET.fromstring(expand())
    for link in model.findall('link'):
        # Knuckles carry inertia only; all other links have separate geometries.
        if not link.get('name').endswith('_knuckle'):
            for tag in ('visual', 'collision'):
                shape = link.find(f'{tag}/geometry')[0]
                for value in shape.attrib.values():
                    assert all(math.isfinite(float(x)) and float(x) > 0
                               for x in value.split())
        mass = float(link.find('inertial/mass').get('value'))
        assert math.isfinite(mass) and mass > 0
        inertia = link.find('inertial/inertia')
        values = {key: float(value) for key, value in inertia.attrib.items()}
        assert all(math.isfinite(value) for value in values.values())
        assert all(values[key] == 0 for key in ('ixy', 'ixz', 'iyz'))
        diagonal = [values[key] for key in ('ixx', 'iyy', 'izz')]
        assert min(diagonal) > 0
        assert 2 * max(diagonal) <= sum(diagonal)
