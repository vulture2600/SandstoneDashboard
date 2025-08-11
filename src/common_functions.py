"""Common functions for SandstoneDashboard"""

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
