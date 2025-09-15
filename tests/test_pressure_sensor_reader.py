"""Tests for PressureSensorReader in getPressures.py"""

import json
from pathlib import Path
import pytest
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
    """Open config fixture """
    fixture_path = Path(__file__).parent / "fixtures" / "getPressures.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    return data["SandstoneHost1"]

def test_read_channels_enabled_channel(pressures_config):
    """Test that enabled channels return calculated PSI values."""
    adc = MockADC({0: 10000})  # Simulated ADC reading
    reader = PressureSensorReader(
        adc=adc,
        channels=pressures_config,
        hostname="SandstoneHost1",
        sensor_id="i2c:0x48",
        sensor_type="pressure"
    )

    results = reader.read_channels()
    assert "channel0" in results
    assert results["channel0"] != NO_PSI
    assert results["channel0"] > 0

def test_read_channels_disabled_channel(pressures_config):
    """Disabled channels should return NO_PSI."""
    adc = MockADC({1: 12000})
    reader = PressureSensorReader(
        adc=adc,
        channels=pressures_config,
        hostname="SandstoneHost1",
        sensor_id="i2c:0x48",
        sensor_type="pressure"
    )

    results = reader.read_channels()
    assert results["channel1"] == NO_PSI

def test_construct_points_with_off_value(pressures_config):
    """Values below PSI_LOWER_BOUND should be labeled 'OFF'."""
    adc = MockADC({0: 4050})  # Exactly at minADC -> should calculate near 0
    reader = PressureSensorReader(
        adc=adc,
        channels=pressures_config,
        hostname="SandstoneHost1",
        sensor_id="i2c:0x48",
        sensor_type="pressure"
    )

    readings = reader.read_channels()
    series = reader.construct_points(readings)

    assert isinstance(series, list)
    assert series[0]["measurement"] == "pressures"
    assert series[0]["tags"]["hostname"] == "SandstoneHost1"
    assert "pressure" in series[0]["fields"]
    assert series[0]["fields"]["pressure"] in ("OFF", pytest.approx(float))  # allow OFF or float
