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
yamllint deploy_app_playbook.yaml                         # yaml lint check

ansible-lint deploy_app_playbook.yaml                     # ansible lint check

ansible-playbook deploy_app_playbook.yaml --syntax-check  # check for syntax errors
```

Preflight check

```shell
# Dry run, show what will change:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors --diff --check

# Add -t <tag> to limit what runs.
```

Run the playbook, see [vars.yaml](vars.yaml)

```shell
# Create Python virtual env, install packages:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors -t pip

# Deploy dotenv file:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors -t dotenv

# Deploy Python files:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors -t app_files

# Deploy systemd services:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors -t systemd

# Verify systemd services:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors -t verify_services

# Run all parts:
ansible-playbook deploy_app_playbook.yaml -i inventory.ini -l monitors

# Add --check to see which tasks will make changes.

# Add --diff to see the changes.
```

#### Ansible inventory file example

inventory.ini

```ini
[monitors]
HOSTNAME ansible_host=FQDN_HOSTNAME ansible_user=SSH_USER ansible_port=PORT dotenv_host=HOSTNAME
```
