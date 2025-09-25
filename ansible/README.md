# Ansible

## Setup

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

#### Ansible Vault

Some files and variables may be encrypted. Do not decrypt .vault files in place.
The .gitignore file should include the .env file but not when ending with .vault  
If needed, use 'view' instead of 'edit' and redirect stdout to .env without the .vault 

```shell
# If using a password file, the permissions should be 600:
chmod 600 ~/.vault_pass.txt

# Encrypt and rename a dotenv file:
ansible-vault encrypt .env --vault-password-file ~/.vault_pass.txt
mv .env .env.vault

# Edit a dotenv file:
ansible-vault edit vault/.env.somehostname.vault --vault-password-file ~/.vault_pass.txt
```

#### Ansible inventory file example

inventory.ini

```ini
[shed]
HOSTNAME ansible_host=[FQDN_HOSTNAME or IP ADDR] ansible_user=SSH_USER ansible_port=PORT

[stagewall]
HOSTNAME ansible_host=[FQDN_HOSTNAME or IP ADDR] ansible_user=SSH_USER ansible_port=PORT

[schoolroom]
HOSTNAME ansible_host=[FQDN_HOSTNAME or IP ADDR] ansible_user=SSH_USER ansible_port=PORT
```

shed, stagewall, and schoolroom are host groups; additional hosts can be added to each.


## Deploy

#### Linting & syntax checks

```shell
ansible-lint your_playbook.yaml
```

Preflight check

* See [vars.yaml](vars.yaml) for variables
* To see the diffs to be / being made, add **--diff**
* To actually run the playbook, remove **--check**
* To limit host groups, add something like **-l shed** or **-l shed,schoolroom**

#### Deploy the SandstoneDashboard app

```shell
# Create Python virtual env, install packages:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -t pip --check

# Deploy dotenv file:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -t dotenv --vault-password-file ~/.vault_pass.txt --check

# Deploy Python files:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -t app_files --check

# Deploy systemd services:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -t systemd --check

# Deploy logrotate config, create log files:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -t logging --check
```

```shell
# Run all parts against all hosts:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini --vault-password-file ~/.vault_pass.txt --check
```

```shell
# Verify systemd services:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -t verify_services
```

#### Install Promtail and Prometheus Node Exporter

```shell
# Show which tasks will make changes:
ansible-playbook install_promtail_node_exporter.yaml -i inventory.ini --vault-password-file ~/.vault_pass.txt --check
```
