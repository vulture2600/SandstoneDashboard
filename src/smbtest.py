from smb.SMBConnection import SMBConnection

# SMB server details
server_ip = '192.168.30.10'  # e.g., '192.168.1.100'
share_name = 'Public'  # The name of the SMB share    
username = 'Sandstone'
password = 'Sandstone1'  # Your SMB username and password
client_name = 'raspberrypi_client' # A name for your client

try:
    # Create an SMB connection object
    conn = SMBConnection(username, password, client_name, server_ip, use_ntlm_v2=True)

    # Establish the connection
    connected = conn.connect(server_ip, 445) # Port 445 is standard for SMB

    if connected:
        print(f"Successfully connected to {server_ip}!")

        # List files in the root of the share
        file_list = conn.listPath(share_name, '/')
        print(f"Files in '{share_name}':")
        for f in file_list:
            print(f.filename)

        # Close the connection
        conn.close()
        print("Connection closed.")
    else:
        print(f"Failed to connect to {server_ip}.")

except Exception as e:
    print(f"An error occurred: {e}")