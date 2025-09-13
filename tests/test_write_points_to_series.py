"""Tests for write_points_to_series in getTemps.py"""
from src.getTemps import TempUtils, write_points_to_series

def test_write_points_to_series(monkeypatch):
    """Check that points are constructed correctly with different temp readings."""

    # Example room_sensor_map
    room_sensor_map = {
        "room1": {"id": "28-000000000001", "title": "Room 1"},
        "room2": {"id": "28-000000000002", "title": "Room 2"},
        "room3": {"id": "28-000000000003"}  # missing title, should default to Untitled
    }

    hostname = "testhost"

    # Mock read_temp: room1 returns valid temp, room2 fails (None), room3 returns valid
    temp_results = {
        "28-000000000001": 72.0,
        "28-000000000002": None,
        "28-000000000003": 68.0
    }
    monkeypatch.setattr(TempUtils, "read_temp", lambda path: temp_results[path.split('/')[-2]])

    points = write_points_to_series(room_sensor_map, hostname)

    # Should have 3 points
    assert len(points) == 3

    # room1: working, status On
    assert points[0]["tags"]["location"] == "room1"
    assert points[0]["fields"]["temp_flt"] == 72.0
    assert points[0]["tags"]["status"] == "On"

    # room2: failed reading, status OFF, temp -999.9
    assert points[1]["tags"]["location"] == "room2"
    assert points[1]["fields"]["temp_flt"] == -999.9
    assert points[1]["tags"]["status"] == "OFF"

    # room3: missing title, should default to "Untitled"
    assert points[2]["tags"]["title"] == "Untitled"
    assert points[2]["fields"]["temp_flt"] == 68.0
    assert points[2]["tags"]["status"] == "On"
