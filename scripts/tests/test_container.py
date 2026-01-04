#!/usr/bin/env python3
"""Infrastructure validation tests using testinfra."""

import os

import pytest
import testinfra


@pytest.fixture(scope="module")
def host(request: pytest.FixtureRequest) -> testinfra.host.Host:
    """Create testinfra host fixture."""
    image = request.config.getoption("--image", default="ghcr.io/my-org/cpp:noble-stable-latest")
    return testinfra.get_host(f"docker://{image}")


pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION"),
    reason="Container tests are integration-only",
)


def test_python_runtime_exists(host: testinfra.host.Host) -> None:
    """Verify the symlinked Python runtime exists."""
    python = host.file("/app/python_runtime")
    assert python.exists
    assert python.is_symlink


def test_pixi_env_json_exists(host: testinfra.host.Host) -> None:
    """Verify the frozen environment JSON was created."""
    env_json = host.file("/app/pixi_env.json")
    assert env_json.exists
    assert env_json.size > 0


def test_entrypoint_exists(host: testinfra.host.Host) -> None:
    """Verify the entrypoint script exists."""
    entrypoint = host.file("/app/entrypoint.py")
    assert entrypoint.exists


def test_environment_pack_exists(host: testinfra.host.Host) -> None:
    """Verify the pixi-pack tarball was generated."""
    pack = host.file("/app/environment.tar.gz")
    assert pack.exists
    assert pack.size > 0


def test_cmake_available(host: testinfra.host.Host) -> None:
    """Verify CMake is in the environment."""
    cmd = host.run("/app/python_runtime /app/entrypoint.py cmake --version")
    assert cmd.rc == 0
    assert "cmake version" in cmd.stdout.lower()


def test_ninja_available(host: testinfra.host.Host) -> None:
    """Verify Ninja is in the environment."""
    cmd = host.run("/app/python_runtime /app/entrypoint.py ninja --version")
    assert cmd.rc == 0


def test_gcc_available(host: testinfra.host.Host) -> None:
    """Verify GCC is in the environment."""
    cmd = host.run("/app/python_runtime /app/entrypoint.py gcc --version")
    assert cmd.rc == 0
    assert "gcc" in cmd.stdout.lower()
