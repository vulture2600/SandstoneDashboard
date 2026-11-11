"""Tests for SHT30 sensor calculations and data point construction in getSHT30.py"""

import struct

def calculate_sht30_readings(i2c_block_data):
    """Helper representing the calculation logic inside getSHT30.py"""
    if len(i2c_block_data) < 5:
        return None, None

    temp_MSB, temp_LSB = i2c_block_data[0:2]
    humidity_MSB, humidity_LSB = i2c_block_data[3:5]

    raw_temp = struct.unpack(">H", bytes([temp_MSB, temp_LSB]))[0]
    temp_C = -45 + (175 * raw_temp / 65535.0)
    temp_F = temp_C * 1.8 + 32

    raw_hum = struct.unpack(">H", bytes([humidity_MSB, humidity_LSB]))[0]
    humidity = 100 * raw_hum / 65535.0

    return round(temp_F, 2), round(humidity, 2)

def construct_sht30_point(sensor_location, sensor_id, sensor_title, hostname, temp_F, humidity):
    """Helper representing the data point construction logic in getSHT30.py"""
    return {
        "measurement": "temps",
        "tags": {
            "sensor":   1,
            "location": sensor_location,
            "id":       sensor_id,
            "type":     "sht30",
            "title":    sensor_title,
            "hostname": hostname,
            "status":   "ON"
        },
        "fields": {
            "temp_flt": temp_F,
            "humidity_flt": humidity
        }
    }

def test_sht30_calculations():
    """Test raw I2C block data conversion to correct temperature (°F) and humidity (%)"""
    # Example raw I2C block data bytes:
    # Temperature bytes + checksum + Humidity bytes + checksum
    # Let's test with a known conversion value
    # E.g., raw_temp corresponding to ~25°C (77°F), raw_hum corresponding to ~50%

    # 25°C calculation: raw_temp = (25 + 45) * 65535 / 175 ≈ 26214 (0x6666)
    # 50% humidity calculation: raw_hum = 50 * 65535 / 100 ≈ 32767 (0x7FFF)

    temp_bytes = list(struct.pack(">H", 26214)) # [0x66, 0x66]
    hum_bytes = list(struct.pack(">H", 32767))  # [0x7F, 0xFF]

    i2c_block_data = temp_bytes + [0x00] + hum_bytes + [0x00]

    temp_F, humidity = calculate_sht30_readings(i2c_block_data)

    assert temp_F is not None
    assert humidity is not None
    assert 76.9 <= temp_F <= 77.1
    assert 49.9 <= humidity <= 50.1

def test_sht30_point_construction():
    """Test that InfluxDB data points are correctly structured with all required tags and fields."""
    sensor_location = "office"
    sensor_id = "i2c:0x44"
    sensor_title = "Office Sensor"
    hostname = "testhost"
    temp_F = 72.5
    humidity = 45.0

    point = construct_sht30_point(sensor_location, sensor_id, sensor_title, hostname, temp_F, humidity)

    assert point["measurement"] == "temps"
    assert point["tags"]["location"] == "office"
    assert point["tags"]["id"] == "i2c:0x44"
    assert point["tags"]["type"] == "sht30"
    assert point["tags"]["title"] == "Office Sensor"
    assert point["tags"]["hostname"] == "testhost"
    assert point["tags"]["status"] == "ON"
    assert point["fields"]["temp_flt"] == 72.5
    assert point["fields"]["humidity_flt"] == 45.0

def test_invalid_i2c_block_data():
    """Test handling of incomplete or short I2C block data."""
    short_data = [0x66, 0x66, 0x00]
    temp_F, humidity = calculate_sht30_readings(short_data)
    assert temp_F is None
    assert humidity is None
