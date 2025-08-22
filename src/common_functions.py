"""Common functions for SandstoneDashboard"""

import json
import os
import tempfile
from datetime import datetime
import smbclient
from dotenv import load_dotenv
from influxdb import InfluxDBClient

def choose_dotenv(hostname):
    """Choose and load the dotenv file"""

    if 'INVOCATION_ID' in os.environ:
        print(f"Running under Systemd, using .env.{hostname} file")
        load_dotenv(override=True, dotenv_path=f".env.{hostname}")
    else:
        print("Using .env file")
        load_dotenv(override=True)

def database_connect(influxdb_host, influxdb_port, username, password, database):
    """Connect to the database, create if it doesn't exist"""

    print(f"Connecting InfluxDB: {influxdb_host}")
    client = InfluxDBClient(influxdb_host, influxdb_port, username, password, database)
    databases = client.get_list_database()

    if not any(db['name'] == database for db in databases):
        print(f"Creating {database}")
        client.create_database(database)
        client.switch_database(database)

    print(f"InfluxDB client ok! Using {database}")

    return client

class SMBFileTransfer:
    """Create connection to SMB share and copy files"""

    def __init__(self, server, port, share, remote_dir, username, password, config_file_name, config_file):
        self.server = server
        self.port = port
        self.share = share
        self.remote_dir = remote_dir
        self.username = username
        self.password = password
        self.config_file_name = config_file_name
        self.config_file = config_file
        self.remote_file = f"\\\\{self.server}\\{self.share}\\{self.remote_dir}\\{self.config_file_name}"

    def connect(self):
        """Connect to the SMB server"""

        try:
            smbclient.register_session(
                self.server,
                port = self.port,
                username=self.username,
                password=self.password
                )
            print(f"Connected to SMB server: {self.server}")
            return True

        except (OSError, PermissionError) as e:
            print(f"Connection error to {self.server}: {e}")
        except Exception as e:
            print(f"Unknown error while connecting to {self.server}: {e}")
        return False

    def get_json_config(self):
        """
        Get JSON config via smbclient.
        Only overwrite local file if remote is newer or local is missing,
        and JSON is valid.
        """

        try:
            stat = smbclient.stat(self.remote_file)
            remote_mtime = datetime.fromtimestamp(stat.st_mtime)

            update_needed = (
                remote_mtime > datetime.fromtimestamp(os.path.getmtime(self.config_file))
                if os.path.exists(self.config_file)
                else True
            )

            if not update_needed:
                print("Local config is up to date")
                return True

            with smbclient.open_file(self.remote_file, "r", encoding="utf-8") as open_smb_file:
                smb_file_content = open_smb_file.read()

            json.loads(smb_file_content) # validate json

            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
                tmp.write(smb_file_content)

            os.replace(tmp.name, self.config_file)

            print("Local config updated from remote")
            return True

        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {self.remote_file} - {e}")
        except Exception as e:
            print(f"Error fetching config: {e}")
        return False

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
    except Exception as e:
        print(f"An unexpected error has occurred: {e}")
    return {}
