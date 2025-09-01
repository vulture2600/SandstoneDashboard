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

#### Ansible Vault

Do not decrypt .vault files in place; .gitignore covers .env files but not those ending with .vault

If you need a decrypted file, use 'view' instead of 'edit' and redirect stdout to .env.somehostname without the .vault 

```shell
# If using a password file, the permissions should be 600:
chmod 600 ~/.vault_pass.txt

# Encrypt and rename a dotenv file:
ansible-vault encrypt .env.somehostname --vault-password-file ~/.vault_pass.txt
mv .env.somehostname .env.somehostname.vault

# Edit a dotenv file:
ansible-vault edit vault/.env.somehostname.vault --vault-password-file ~/.vault_pass.txt
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

Run the playbook

* See [vars.yaml](vars.yaml) for variables
* To see which tasks will make changes, add **--check**
* To see the changes, add **--diff**

```shell
# Create Python virtual env, install packages:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t pip

# Deploy dotenv file:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t dotenv --vault-password-file ~/.vault_pass.txt

# Deploy Python files:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t app_files

# Deploy systemd services:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t systemd

# Deploy logrotate config, create log files:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini -l shed -t logging
```

```shell
# Run all parts against all hosts. Remove --check to really do this:
ansible-playbook deploy_sandstonedashboard.yaml -i inventory.ini --vault-password-file ~/.vault_pass.txt --check
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

shed, stagewall, and schoolroom are host groups; additional hosts can be added to each.
