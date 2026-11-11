"""Tests for PressureSensorReader in getPressures.py"""

import json
import sys
from pathlib import Path
import pytest

# Mock hardware-specific module if not installed in test environment
if "Adafruit_ADS1x15" not in sys.modules:
    from unittest.mock import MagicMock
    sys.modules["Adafruit_ADS1x15"] = MagicMock()

from src.getPressures import PressureSensorReader, NO_PSI

class MockADC:
    """Fake ADC device to simulate hardware behavior."""
    def __init__(self, values):
        self.values = values

    def read_adc(self, ch_num, gain):
        """Test for reading adc"""
        return self.values.get(ch_num, 0)

@pytest.fixture
def pressures_config():
    """Open config fixture"""
    fixture_path = Path(__file__).parent / "fixtures" / "getPressures.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    return data["SandstoneHost1"]

def test_read_channels_enabled_channel(pressures_config):
    """Test that enabled channels return calculated PSI values."""
    adc = MockADC({0: 13200})  # Simulated ADC reading
    reader = PressureSensorReader(
        adc=adc,
        channels=pressures_config,
        hostname="SandstoneHost1",
        sensor_id="i2c:0x48",
        sensor_type="ADS1115"
    )

    results = reader.read_channels()
    assert "channel0" in results
    assert results["channel0"] != NO_PSI

    # Calculate expected PSI dynamically from fixture parameters
    cfg = pressures_config["channel0"]
    expected_psi = (
        (13200 - cfg["ch_minADC"]) *
        (cfg["ch_maxPSI"] - cfg["ch_minPSI"]) /
        (cfg["ch_maxADC"] - cfg["ch_minADC"]) +
        cfg["ch_minPSI"]
    )
    assert results["channel0"] == expected_psi

def test_read_channels_disabled_channel(pressures_config):
    """Disabled channels should return NO_PSI."""
    adc = MockADC({1: 12000})
    reader = PressureSensorReader(
        adc=adc,
        channels=pressures_config,
        hostname="SandstoneHost1",
        sensor_id="i2c:0x48",
        sensor_type="ADS1115"
    )

    results = reader.read_channels()
    assert results["channel1"] == NO_PSI

def test_construct_points(pressures_config):
    """Test that InfluxDB points are constructed correctly from readings."""
    adc = MockADC({0: 13200})
    reader = PressureSensorReader(
        adc=adc,
        channels=pressures_config,
        hostname="SandstoneHost1",
        sensor_id="i2c:0x48",
        sensor_type="ADS1115"
    )

    cfg = pressures_config["channel0"]
    expected_psi = (
        (13200 - cfg["ch_minADC"]) *
        (cfg["ch_maxPSI"] - cfg["ch_minPSI"]) /
        (cfg["ch_maxADC"] - cfg["ch_minADC"]) +
        cfg["ch_minPSI"]
    )

    readings = {"channel0": expected_psi, "channel1": NO_PSI}
    series = reader.construct_points(readings)

    assert len(series) >= 1

    # Check channel0 point against fixture values
    ch0_point = next(p for p in series if p["tags"]["channel"] == 0)
    assert ch0_point["measurement"] == "pressures"
    assert ch0_point["tags"]["location"] == cfg["channel_ID"]
    assert ch0_point["tags"]["title"] == cfg["channel_name"]
    assert ch0_point["tags"]["id"] == "i2c:0x48"
    assert ch0_point["tags"]["type"] == "ADS1115"
    assert ch0_point["tags"]["hostname"] == "SandstoneHost1"
    assert ch0_point["fields"]["pressure_flt"] == expected_psi
    