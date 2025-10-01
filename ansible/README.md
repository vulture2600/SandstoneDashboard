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
# If using a vault password file, the permissions should be 600:
chmod 600 ~/.vault_pass.txt
```

Ansible commands reference [ansible.cfg](ansible.cfg) for the vault_password_file parameter.

```shell
# Encrypt and rename a dotenv file:
ansible-vault encrypt .env
mv .env .env.vault

# Edit a dotenv file:
ansible-vault edit vault/.env.somehostname.vault
```

#### Ansible inventory file example

inventory.yaml

```yaml
all:
  hosts:
    shed:
      ansible_host: hostname1
      ansible_user: grigri
      ansible_port: 22
    stagewall:
      ansible_host: hostname2
      ansible_user: grigri
      ansible_port: 22
    schoolroom:
      ansible_host: hostname3
      ansible_user: grigri
      ansible_port: 22
    weatherstation:
      ansible_host: hostname4
      ansible_user: grigri
      ansible_port: 22
  children:
    getTemps:
      hosts:
        shed:
          ansible_host: hostname1
          ansible_user: grigri
          ansible_port: 22
        stagewall:
          ansible_host: hostname2
          ansible_user: grigri
          ansible_port: 22
        schoolroom:
          ansible_host: hostname3
          ansible_user: grigri
          ansible_port: 22
        weatherstation:
          ansible_host: hostname4
          ansible_user: grigri
          ansible_port: 22
    getPressures:
      hosts:
        shed:
          ansible_host: hostname1
          ansible_user: grigri
          ansible_port: 22
    getSHT30:
      hosts:
        shed:
          ansible_host: hostname1
          ansible_user: grigri
          ansible_port: 22
    getWeather:
      hosts:
        shed:
          ansible_host: hostname1
          ansible_user: grigri
          ansible_port: 22
```

getTemps, getPressures, getSHT30, and getWeather are host groups. Hosts can be added or removed from each.


## Deploy

#### Linting & syntax checks

```shell
ansible-lint playbooks/your_playbook.yaml
```

Preflight check

* See [vars.yaml](inventory/group_vars/all/vars.yaml) for variables
* To see the diffs add **--diff**
* To actually run the playbook, remove **--check**
* To limit host groups, add something like **-l shed** or **-l shed,schoolroom**

#### Deploy the SandstoneDashboard app

```shell
# Create Python virtual env, install packages, create directories, etc:
ansible-playbook playbooks/deploy_sandstonedashboard.yaml -t common --check

# Deploy getPressure service:
ansible-playbook playbooks/deploy_sandstonedashboard.yaml -t getPressure --check

# Deploy getSHT30 service:
ansible-playbook playbooks/deploy_sandstonedashboard.yaml -t getSHT30 --check

# Deploy getTemps service:
ansible-playbook playbooks/deploy_sandstonedashboard.yaml -t getTemps --check

# Deploy getWeather service:
ansible-playbook playbooks/deploy_sandstonedashboard.yaml -t getWeather --check
```

#### Install Promtail and Prometheus Node Exporter

```shell
ansible-playbook playbooks/install_promtail_node_exporter.yaml --check
```
