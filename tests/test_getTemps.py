"""Tests for getTemps.py"""

import json
import os
import pytest

@pytest.fixture
def sample_config():
    """Open test getTemps.json"""
    with open(os.path.join("tests", "fixtures", "getTemps.json")) as f:
        return json.load(f)

@pytest.fixture
def sensors(sample_config):
    """Import src.getTemps.GetTempSensors"""
    from src.getTemps import GetTempSensors
    s = GetTempSensors(sample_config, hostname="SandstoneHost3")
    return s

def test_assigned_sensors_json_only(sensors):
    """Only assigned sensors from JSON for SandstoneHost3 should be in rooms."""

    # Populate assigned sensors
    sensors.get_assigned_sensors()

    # Get rooms
    rooms = sensors.rooms
    assert isinstance(rooms, dict)

    # Expected IDs from JSON
    expected_ids = {"28-000000000007", "28-000000000008", "28-000000000009"}
    actual_ids = {v["id"] for v in rooms.values()}

    assert actual_ids == expected_ids, (
        f"Expected IDs {expected_ids} but got {actual_ids}"
    )

    # Optional: check that room titles match
    expected_titles = {"Room 7", "Room 8", "Room 9"}
    actual_titles = {v["title"] for v in rooms.values()}
    assert actual_titles == expected_titles
