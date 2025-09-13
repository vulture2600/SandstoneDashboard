"""Tests for GetTempSensors in getTemps.py"""

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

    rooms = sensors.rooms
    assert isinstance(rooms, dict)

    # Expected IDs from JSON
    expected_ids = {"28-000000000007", "28-000000000008", "28-000000000009"}
    actual_ids = {v["id"] for v in rooms.values()}

    assert actual_ids == expected_ids, (
        f"Expected IDs {expected_ids} but got {actual_ids}"
    )

    # Check that room titles match
    expected_titles = {"Room 7", "Room 8", "Room 9"}
    actual_titles = {v["title"] for v in rooms.values()}
    assert actual_titles == expected_titles

def test_attached_sensors(monkeypatch, sensors):
    """Attached sensors should be filtered correctly by SENSOR_PREFIX."""

    # Fake directory contents
    fake_devices = [
        "28-000000000008",
        "28-000000000009",
        "28-000000000010",
        "28-000000000011"
    ]

    # Monkeypatch os.listdir to return our fake devices
    monkeypatch.setattr(os, "listdir", lambda path: fake_devices)

    sensors.get_attached_sensors()

    # Only IDs with prefix should remain
    expected_ids = ["28-000000000008", "28-000000000009", "28-000000000010", "28-000000000011"]
    assert sensors.sensor_ids == expected_ids, (
        f"Expected {expected_ids} but got {sensors.sensor_ids}"
    )

    # Ensure unassigned_ids is still untouched
    assert sensors.unassigned_ids == []

def test_find_unassigned_sensors(monkeypatch, sensors):
    """find_unassigned_sensors() correctly identifies attached sensors not in config."""

    # Populate assigned sensors from JSON
    sensors.get_assigned_sensors()

    # Step 2: Fake attached devices (two in config, two extra)
    fake_devices = [
        "28-000000000008",  # in JSON
        "28-000000000009",  # in JSON
        "28-000000000010",  # not in JSON
        "28-000000000011"   # not in JSON
    ]
    monkeypatch.setattr(os, "listdir", lambda path: fake_devices)

    # Populate sensor_ids
    sensors.get_attached_sensors()

    # Call method under test
    sensors.find_unassigned_sensors()

    # Assert unassigned_ids are those not in JSON
    expected_unassigned = ["28-000000000010", "28-000000000011"]
    assert sensors.unassigned_ids == expected_unassigned, (
        f"Expected unassigned {expected_unassigned} but got {sensors.unassigned_ids}"
    )

def test_combine_unassigned_assigned(monkeypatch, sensors):
    """combine_unassigned_assigned() adds unassigned attached sensors to rooms."""

    # Populate assigned sensors from JSON
    sensors.get_assigned_sensors()

    # Fake attached devices (two in JSON, two extra)
    fake_devices = [
        "28-000000000008",  # in JSON
        "28-000000000009",  # in JSON
        "28-000000000010",  # not in JSON
        "28-000000000011"   # not in JSON
    ]
    monkeypatch.setattr(os, "listdir", lambda path: fake_devices)

    # Populate sensor_ids
    sensors.get_attached_sensors()

    # Identify unassigned sensors
    sensors.find_unassigned_sensors()

    # Combine assigned + unassigned
    sensors.combine_unassigned_assigned()

    # Assert rooms now include unassigned sensors
    expected_unassigned_keys = {"Unassigned1", "Unassigned2"}
    actual_unassigned_keys = {k for k in sensors.rooms.keys() if k.startswith("Unassigned")}
    assert actual_unassigned_keys == expected_unassigned_keys, (
        f"Expected unassigned keys {expected_unassigned_keys} but got {actual_unassigned_keys}"
    )

    # Assert the IDs match the unassigned_ids
    for idx, sid in enumerate(sensors.unassigned_ids, start=1):
        key = f"Unassigned{idx}"
        assert sensors.rooms[key]["id"] == sid
        assert sensors.rooms[key]["title"] == "Untitled"
