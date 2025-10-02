# Ansible

## Setup

#### Key pair for SSH 

Ansible uses ssh to connect.

```shell
# Create a public/private key pair on the local machine as the Ansible user:
ssh-keygen

# Append the public key to the remote authorized_keys file:
ssh-copy-id -i your_key.pub -p 22 username@remote_host

# ssh-copy-id does the following:
# Copy the public key to the remote host and append to ~/.ssh/authorized_keys
# Set permissions of ~/.ssh to 700
# Set permissions of ~/.ssh/authorized_keys to 600
```

#### Ansible Vault

Some files and variables may be encrypted. Do not decrypt .vault files in place.  
The [.gitignore](../.gitignore) file should ignore .env but not .env.vault  
If needed, use 'view' instead of 'edit' and redirect stdout to .env without the .vault 

```shell
# If using a vault password file, the permissions should be 600.
chmod 600 ~/.vault_pass.txt
```

Ansible commands reference [ansible.cfg](ansible.cfg) for the vault password file (vault_password_file).

```shell
# Encrypt and rename a dotenv file:
ansible-vault encrypt .env
mv .env .env.vault

# Edit a dotenv file:
ansible-vault edit .env.vault

# Decrypt and redirect stdout to .env:
ansible-vault view .env.vault > .env
```

#### Ansible inventory file example

inventory.yaml

```yaml
all:
  hosts:
    shed:
      ansible_host: host1
      ansible_user: grigri
      ansible_port: 22
    stagewall:
      ansible_host: host2
      ansible_user: grigri
      ansible_port: 22
    schoolroom:
      ansible_host: host3
      ansible_user: grigri
      ansible_port: 22
    weatherstation:
      ansible_host: host4
      ansible_user: grigri
      ansible_port: 22
  children:
    getTemps:
      hosts:
        shed:
          ansible_host: host1
          ansible_user: grigri
          ansible_port: 22
        stagewall:
          ansible_host: host2
          ansible_user: grigri
          ansible_port: 22
        schoolroom:
          ansible_host: host3
          ansible_user: grigri
          ansible_port: 22
        weatherstation:
          ansible_host: host4
          ansible_user: grigri
          ansible_port: 22
    getPressures:
      hosts:
        shed:
          ansible_host: host1
          ansible_user: grigri
          ansible_port: 22
    getSHT30:
      hosts:
        shed:
          ansible_host: host1
          ansible_user: grigri
          ansible_port: 22
    getWeather:
      hosts:
        shed:
          ansible_host: host1
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
