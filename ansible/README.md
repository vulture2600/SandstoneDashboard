# Ansible

#### Create key pair for ssh 

Ansible uses ssh to connect. Create a key pair if one doesn't already exist.

```shell
# Create a public/private key pair:
ssh-keygen

# Append the PUBLIC key, e.g. id_ed25519.pub, to ~/.ssh/authorized_keys on the remote machine.

# Verify permissions are correct:
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# The local user might need to logout/login before ssh uses the key.
```

#### Manage the Raspberry Pi's

Linting & syntax checks

```shell
yamllint deploy_sandstonedashboard.yaml                         # yaml lint check

ansible-lint deploy_sandstonedashboard.yaml                     # ansible lint check

ansible-playbook deploy_sandstonedashboard.yaml --syntax-check  # check for syntax errors
```

Preflight check

```shell
# Dry run, show what will change:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed --diff --check

# Add -t <tag> to limit which tasks runs.
```

Run the playbook, see [vars.yaml](vars.yaml) for variables.

* To see which tasks will make changes, add **--check**
* To see the changes, add **--diff**

```shell
# Create Python virtual env, install packages:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t pip

# Deploy dotenv file:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t dotenv

# Deploy Python files:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t app_files

# Deploy systemd services:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t systemd

# Deploy logrotate config, create log files:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t logging
```

```shell
# Run all parts:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed
```

```shell
# Verify systemd services:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t verify_services
```

#### Ansible inventory file example

inventory.ini

```ini
[shed]
HOSTNAME ansible_host=[FQDN_HOSTNAME or IP ADDR] ansible_user=SSH_USER ansible_port=PORT dotenv_host=HOSTNAME

[stagewall]
HOSTNAME ansible_host=[FQDN_HOSTNAME or IP ADDR] ansible_user=SSH_USER ansible_port=PORT dotenv_host=HOSTNAME

[schoolroom]
HOSTNAME ansible_host=[FQDN_HOSTNAME or IP ADDR] ansible_user=SSH_USER ansible_port=PORT dotenv_host=HOSTNAME
```
