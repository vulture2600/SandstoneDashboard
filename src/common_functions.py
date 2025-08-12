"""Common functions for SandstoneDashboard"""

import json
from influxdb import InfluxDBClient

def database_connect(influxdb_host, influxdb_port, username, password, database):
    """Connect to the database, create if it doesn't exist"""

    print("Connecting to the database")
    client = InfluxDBClient(influxdb_host, influxdb_port, username, password, database)
    databases = client.get_list_database()

    if not any(db['name'] == database for db in databases):
        print(f"Creating {database}")
        client.create_database(database)
        client.switch_database(database)

    print(f"InfluxDB client ok! Using {database}")

    return client

def load_json_file(json_file):
    """Load json file, handle exceptions"""
    try:
        with open(json_file, encoding='utf-8') as open_json_file:
            return json.load(open_json_file)
    except FileNotFoundError:
        print(f"File not found: {json_file}")
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {json_file}: {e}")
    except OSError as e:
        print(f"Error opening {json_file}: {e}")
    return {}
