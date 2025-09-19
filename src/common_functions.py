"""Common functions for SandstoneDashboard"""

import json
import logging
import os
import tempfile
from datetime import datetime
import smbclient
from dotenv import load_dotenv
import influxdb_client
from influxdb_client.client.exceptions import InfluxDBError
from influxdb import InfluxDBClient

logging.getLogger("smbprotocol").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def choose_dotenv(hostname):
    """Choose and load the dotenv file"""

    if 'INVOCATION_ID' in os.environ:
        logger.info(f"Running under Systemd, using .env.{hostname}")
        load_dotenv(override=True, dotenv_path=f".env.{hostname}")
    else:
        logger.info("Using .env")
        load_dotenv(override=True)

def database_connect(influxdb_host, influxdb_port, username, password, database):
    """Connect to the database, create if it doesn't exist"""

    logger.info(f"Connecting InfluxDB: {influxdb_host}")
    client = InfluxDBClient(influxdb_host, influxdb_port, username, password, database)
    databases = client.get_list_database()

    if not any(db['name'] == database for db in databases):
        logger.info(f"Creating {database}")
        client.create_database(database)
        client.switch_database(database)

    logger.info(f"InfluxDB client ok! Using {database}")

    return client

def influxdb_connect(influxdb_host, influxdb_port, influxdb_token, influxdb_org, influxdb_bucket):
    """Connect to InfluxDB, create the bucket if it doesn't exist"""

    logger.info(f"Connecting InfluxDB: {influxdb_host}")
    url = f"http://{influxdb_host}:{influxdb_port}"
    client = influxdb_client.InfluxDBClient(url=url, token=influxdb_token, org=influxdb_org)

    buckets_api = client.buckets_api()

    try:
        buckets = buckets_api.find_buckets().buckets
        bucket_names = [b.name for b in buckets]

        if influxdb_bucket not in bucket_names:
            logger.info(f"Bucket '{influxdb_bucket}' not found. Creating it...")
            orgs_api = client.organizations_api()
            org = orgs_api.find_organizations(org=influxdb_org)[0]
            buckets_api.create_bucket(bucket_name=influxdb_bucket, org_id=org.id)
            logger.info(f"Bucket '{influxdb_bucket}' created successfully.")
        else:
            logger.info(f"Bucket '{influxdb_bucket}' already exists.")

    except InfluxDBError as e:
        logger.critical(f"Error checking/creating bucket: {e}")
        raise

    logger.info(f"InfluxDB client ok! Using {influxdb_bucket}")
    return client

def load_json_file(json_file):
    """Load json file, handle exceptions"""
    try:
        with open(json_file, encoding='utf-8') as open_json_file:
            return json.load(open_json_file)
    except FileNotFoundError:
        logger.error(f"File not found: {json_file}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_file}: {e}")
    except OSError as e:
        logger.error(f"Error opening {json_file}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error has occurred: {e}")
    return None

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
            logger.info(f"Connected to SMB server: {self.server}")
            return True

        except (OSError, PermissionError) as e:
            logger.error(f"Connection error to {self.server}: {e}")
        except Exception as e:
            logger.error(f"Unknown error while connecting to {self.server}: {e}")
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
                logger.info(f"Local {self.config_file_name} is already up to date")
                return True

            with smbclient.open_file(self.remote_file, "r", encoding="utf-8") as open_smb_file:
                smb_file_content = open_smb_file.read()

            json.loads(smb_file_content) # validate json

            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
                tmp.write(smb_file_content)

            os.replace(tmp.name, self.config_file)

            logger.info("Local config updated from remote")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {self.remote_file} - {e}")
        except Exception as e:
            logger.error(f"Error fetching config: {e}")
        return False
