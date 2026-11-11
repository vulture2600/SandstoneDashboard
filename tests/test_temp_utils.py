"""Tests for TempUtils in getTemps.py"""

from src.getTemps import TempUtils, TEMP_SENSOR_MODEL
import src.getTemps as get_temps

TITLE = "Test Sensor"
SENSOR_ID = "28-01154f230fa5"


def write_sensor_file(tmp_path, content):
    """Create a 1-Wire sensor directory and its w1_slave device file."""
    sensor_dir = tmp_path / SENSOR_ID
    sensor_dir.mkdir()
    device_file = sensor_dir / get_temps.W1_SLAVE_FILE
    device_file.write_text(content)
    return device_file


# Tests for read_temp()

def test_read_temp_valid(tmp_path, monkeypatch):
    """Valid device file returns correct Fahrenheit temperature"""
    monkeypatch.setattr(get_temps, "W1_DEVICES_PATH", str(tmp_path))
    write_sensor_file(tmp_path, "line1\n2b 01 4b 46 t=18687\n")

    # 18687 → 18.687°C → 65.6°F
    temp = TempUtils.read_temp(SENSOR_ID, TITLE)
    assert temp == 65.6


def test_read_temp_file_not_found(tmp_path, monkeypatch):
    """Nonexistent sensor file returns None"""
    monkeypatch.setattr(get_temps, "W1_DEVICES_PATH", str(tmp_path))
    temp = TempUtils.read_temp(SENSOR_ID, TITLE)
    assert temp is None


def test_read_temp_marker_missing(tmp_path, monkeypatch):
    """File exists but marker 't=' missing returns None"""
    monkeypatch.setattr(get_temps, "W1_DEVICES_PATH", str(tmp_path))
    write_sensor_file(tmp_path, "line1\n2b 01 4b 46 7f ff 7f 10 51\n")

    temp = TempUtils.read_temp(SENSOR_ID, TITLE)
    assert temp is None


def test_read_temp_invalid_value(tmp_path, monkeypatch):
    """File contains invalid number after 't=' returns None"""
    monkeypatch.setattr(get_temps, "W1_DEVICES_PATH", str(tmp_path))
    write_sensor_file(tmp_path, "line1\nt=abc\n")

    temp = TempUtils.read_temp(SENSOR_ID, TITLE)
    assert temp is None


def test_read_temp_too_few_lines(tmp_path, monkeypatch):
    """File with less than 2 lines returns None"""
    monkeypatch.setattr(get_temps, "W1_DEVICES_PATH", str(tmp_path))
    write_sensor_file(tmp_path, "line1\n")

    temp = TempUtils.read_temp(SENSOR_ID, TITLE)
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
        temp=72.5,
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
