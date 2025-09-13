"""Tests for TempUtils in getTemps.py"""

from src.getTemps import TempUtils, TEMP_SENSOR_MODEL

# Tests for read_temp()

def test_read_temp_valid(tmp_path):
    """Valid device file returns correct Fahrenheit temperature"""
    device_file = tmp_path / "sensor"
    # 18687 → 18.687°C → 65.6°F
    device_file.write_text("line1\n2b 01 4b 46 t=18687\n")
    temp = TempUtils.read_temp(str(device_file))
    assert temp == 65.6

def test_read_temp_file_not_found():
    """Nonexistent file returns None"""
    temp = TempUtils.read_temp("/nonexistent/file")
    assert temp is None

def test_read_temp_marker_missing(tmp_path):
    """File exists but marker 't=' missing returns None"""
    device_file = tmp_path / "sensor"
    device_file.write_text("line1\n2b 01 4b 46 7f ff 7f 10 51\n")
    temp = TempUtils.read_temp(str(device_file))
    assert temp is None

def test_read_temp_invalid_value(tmp_path):
    """File contains invalid number after 't=' returns None"""
    device_file = tmp_path / "sensor"
    device_file.write_text("line1\nt=abc\n")
    temp = TempUtils.read_temp(str(device_file))
    assert temp is None

def test_read_temp_too_few_lines(tmp_path):
    """File with less than 2 lines returns None"""
    device_file = tmp_path / "sensor"
    device_file.write_text("line1\n")
    temp = TempUtils.read_temp(str(device_file))
    assert temp is None

# Tests for construct_data_point()

def test_construct_data_point_basic():
    """Returns a dict with expected structure and values"""
    dp = TempUtils.construct_data_point(
        room_id="room1",
        sensor_id="28-000000000001",
        title="Room 1",
        status="ok",
        hostname="host1",
        temp=72.5
    )

    assert "measurement" in dp
    assert "tags" in dp
    assert "fields" in dp

    assert dp["measurement"] == "temps"

    tags = dp["tags"]
    assert tags["location"] == "room1"
    assert tags["id"] == "28-000000000001"
    assert tags["title"] == "Room 1"
    assert tags["status"] == "ok"
    assert tags["hostname"] == "host1"
    assert tags["type"] == TEMP_SENSOR_MODEL

    fields = dp["fields"]
    assert fields["temp_flt"] == 72.5
