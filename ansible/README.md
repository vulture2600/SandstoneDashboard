# Ansible

#### Create key pair for ssh 

Ansible uses ssh to connect. Create a key pair if one doesn't already exist.

```shell
# Create a public/private key pair:
ssh-keygen

# Copy the PUBLIC key (e.g. id_ed25519.pub) to the remote machine and append it to .ssh/authorized_keys

# Verify permissions on authorized_keys are correct:
chmod 600 .ssh/authorized_keys

# The local user might need to logout/login before ssh uses the key.
```

#### Manage the Raspberry Pi's

Linting & syntax checks

```shell
yamllint systemd_playbook.yaml  # yaml lint check

ansible-lint systemd_playbook.yaml  # ansible lint check

ansible-playbook systemd_playbook.yaml --syntax-check  # check for syntax errors
```

Preflight check

```shell
# Dry run, show what will change, only hosts in the monitors group in inventory.ini:
ansible-playbook systemd_playbook.yaml -i inventory.ini -l monitors --diff --check
```

Run the playbook

```shell
# Run the pip (tagged) tasks in the playbook against the monitors group in inventory.ini:
ansible-playbook systemd_playbook.yaml -i inventory.ini -l monitors -t pip

# Run the systemd (tagged) tasks in the playbook against the monitors group in inventory.ini:
ansible-playbook systemd_playbook.yaml -i inventory.ini -l monitors -t systemd

# Run all tasks in the playbook against the monitors group in inventory.ini:
ansible-playbook systemd_playbook.yaml -i inventory.ini -l monitors

# Add --check to see which tasks will make changes.

# Add --diff to see the changes.
```

#### Ansible inventory file example

inventory.ini

```ini
[monitors]
HOSTNAME ansible_host=FQDN_HOSTNAME ansible_user=SSH_USER ansible_port=PORT
```
