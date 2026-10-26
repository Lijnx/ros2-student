#!/usr/bin/env python3
"""Run the PR05 live/MCAP experiment in an otherwise empty ROS domain.

Run after sourcing ROS and install/setup.bash. Existing bags are never replaced.
The output directory defaults to log/pr05-<timestamp>, outside tracked evidence.
"""

import argparse
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import time

import yaml


def run(command, log, expected=0):
    """Capture the actual command, both streams and its exit status."""
    if (command[:2] in (['ros2', 'node'], ['ros2', 'topic'])
            and command[2] in ('list', 'info') and '--no-daemon' not in command):
        command = command + ['--no-daemon', '--spin-time', '2']
    log.write('\n$ ' + shlex.join(map(str, command)) + '\n')
    log.flush()
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, timeout=25)
    log.write(result.stdout + f'\nexit={result.returncode}\n')
    log.flush()
    assert result.returncode == expected, (command, result.returncode, result.stdout)
    return result.stdout


@contextmanager
def process(command, path):
    """Ensure background launch/player/reader processes are always stopped."""
    with path.open('w') as log:
        log.write('$ ' + shlex.join(map(str, command)) + '\n')
        log.flush()
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                 start_new_session=True)
        try:
            yield child
            assert child.poll() is None, f'Process exited early: {path}'
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGINT)
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
                    raise AssertionError(f'Process did not stop cleanly: {path}')
            log.write(f'\nexit={child.returncode}\n')
        assert child.returncode == 0, f'Unclean shutdown: {path}'


def nodes():
    """Avoid stale ros2-daemon graph caches."""
    result = subprocess.run(
        ['ros2', 'node', 'list', '--no-daemon', '--spin-time', '1'],
        text=True, capture_output=True, timeout=10, check=True)
    names = result.stdout.splitlines()
    assert len(names) == len(set(names)), f'Duplicate node names: {names}'
    return set(names)


def wait_nodes(expected):
    """Wait for discovery and verify the exact process composition."""
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        actual = nodes()
        if actual == expected:
            return
        time.sleep(0.5)
    raise AssertionError(f'Unexpected graph: {actual}; expected {expected}')


def echo(reliability):
    """Use explicit policies: automatic CLI QoS would conceal the defect."""
    return ['timeout', '4s', 'ros2', 'topic', 'echo', '/robot_a/sensor_pose',
            'turtlesim_msgs/msg/Pose', '--qos-reliability', reliability, '--once']


def verify_reader(path, reliability, log):
    """Check the application's own callback, not just a CLI subscriber."""
    text = path.read_text()
    counts = [int(x) for x in re.findall(r'received=(\d+)', text)]
    assert counts, f'No reader diagnostics in {path}'
    if reliability == 'reliable':
        assert max(counts) == 0
        assert 'incompatible QoS' in text and 'RELIABILITY' in text
    else:
        assert max(counts) > 0
    log.write(f'\nReader {path.name}: reliability={reliability}, '
              f'max_received={max(counts)}\n')
    log.flush()


def main():
    """Compare both profiles on live data and on exactly one unchanged bag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=Path('log') / time.strftime('pr05-%Y%m%d-%H%M%S'))
    args = parser.parse_args()
    output = args.output.resolve()
    bag = output / 'bag'
    assert not bag.exists(), f'Refusing to replace existing bag: {bag}'
    assert not nodes(), 'Use an empty ROS_DOMAIN_ID; stop other nodes first'
    output.mkdir(parents=True, exist_ok=True)
    launch = ['ros2', 'launch', 'course_bringup', 'patrol.launch.py',
              'namespace:=robot_a', f'bag_dir:={bag}']
    expected = {'/turtlesim', '/robot_a/patrol', '/robot_a/pose_relay',
                '/robot_a/pose_subscriber'}
    with (output / 'qos-before.txt').open('w') as before, \
            (output / 'qos-after.txt').open('w') as after:
        before.write(f'ROS_DISTRO={os.environ.get("ROS_DISTRO")} '
                     f'ROS_DOMAIN_ID={os.environ.get("ROS_DOMAIN_ID", "0")}\n')
        with process(launch + ['subscriber_reliability:=reliable', 'record:=false'],
                     output / 'live-before.log'):
            wait_nodes(expected)
            run(['ros2', 'topic', 'list', '-t'], before)
            run(['ros2', 'topic', 'info', '/robot_a/sensor_pose', '--verbose'], before)
            run(echo('reliable'), before, expected=124)
            assert not bag.exists(), 'record:=false started recording'
        verify_reader(output / 'live-before.log', 'reliable', before)
        wait_nodes(set())

        with process(launch + ['subscriber_reliability:=best_effort', 'record:=true'],
                     output / 'live-after.log'):
            wait_nodes(expected | {'/rosbag2_recorder'})
            run(['ros2', 'node', 'list', '--no-daemon', '--spin-time', '1'], after)
            run(['ros2', 'node', 'info', '/robot_a/patrol'], after)
            run(['ros2', 'topic', 'info', '/robot_a/sensor_pose', '--verbose'], after)
            run(echo('best_effort'), after)
            run(['timeout', '4s', 'ros2', 'topic', 'echo', '/turtle1/cmd_vel',
                 'geometry_msgs/msg/Twist', '--once'], after)
            poses = []
            for _ in range(2):
                text = run(['timeout', '4s', 'ros2', 'topic', 'echo', '/turtle1/pose',
                            'turtlesim_msgs/msg/Pose', '--once'], after)
                poses.append(next(yaml.safe_load_all(text)))
                time.sleep(1)
            assert poses[0]['x'] != poses[1]['x'] or poses[0]['y'] != poses[1]['y']
        verify_reader(output / 'live-after.log', 'best_effort', after)
        wait_nodes(set())

        metadata = (bag / 'metadata.yaml').read_text()
        info = yaml.safe_load(metadata)['rosbag2_bagfile_information']
        assert info['storage_identifier'] == 'mcap'
        topics = info['topics_with_message_count']
        assert len(topics) == 1
        assert topics[0]['topic_metadata']['name'] == '/robot_a/sensor_pose'
        assert topics[0]['message_count'] > 0
        (output / 'bag-metadata.yaml').write_text(metadata)
        files = list(bag.glob('*.mcap'))
        assert len(files) == 1
        digest = hashlib.sha256(files[0].read_bytes()).hexdigest()
        after.write(f'\nMCAP SHA-256 before replay: {digest}\n')
        run(['ros2', 'bag', 'info', str(bag)], after)
        overrides = Path('config/qos-overrides.yaml').resolve()
        with process(['ros2', 'bag', 'play', str(bag), '--loop',
                      '--disable-keyboard-controls', '--progress-bar-update-rate', '0',
                      '--qos-profile-overrides-path', str(overrides)],
                     output / 'replay.log'):
            wait_nodes({'/rosbag2_player'})
            for reliability, log in [('reliable', before), ('best_effort', after)]:
                path = output / f'replay-{reliability}.log'
                with process(['ros2', 'run', 'course_bringup', 'pose_subscriber',
                              '--ros-args', '-r', '__ns:=/robot_a',
                              '-p', f'reliability:={reliability}'], path):
                    wait_nodes({'/rosbag2_player', '/robot_a/pose_subscriber'})
                    run(['ros2', 'topic', 'info', '/robot_a/sensor_pose', '--verbose'], log)
                    run(echo(reliability), log,
                        expected=124 if reliability == 'reliable' else 0)
                    time.sleep(1)
                verify_reader(path, reliability, log)
        wait_nodes(set())
        assert hashlib.sha256(files[0].read_bytes()).hexdigest() == digest
        after.write(f'\nMCAP SHA-256 after both replay checks: {digest}\n'
                    'PASS: live and replay QoS, one unchanged MCAP, clean shutdown.\n')
    print(f'PR05 experiment passed; results: {output}')


if __name__ == '__main__':
    main()
