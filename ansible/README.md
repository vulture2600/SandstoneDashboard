# Ansible

This details the steps required to run Ansible playbooks on the Raspberry Pis along with some basic system configuration.

## Create key pair for SSH 

Ansible uses ssh to connect.

```shell
# Create a public/private key pair on the local machine as the Ansible user:
ssh-keygen

# Append the public key to the remote authorized_keys file:
ssh-copy-id -i your_key.pub -p 22 USERNSME@REMOTE_HOST
```

ssh-copy-id does the following:
* Copies the public key to the remote host and append to ~/.ssh/authorized_keys
* Sets permissions of ~/.ssh to 700
* Sets permissions of ~/.ssh/authorized_keys to 600


## Configure the Raspberry Pi

These steps are mainly for newly reimaged Pis.

#### Sudo without password

```shell
# Allow sudo access without a password:
sudo sh -c "echo 'pi ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/010_pi-nopasswd"

# Set permissions:
sudo chmod 440 /etc/sudoers.d/010_pi-nopasswd

# Verify permissions and parsing:
sudo visudo -c
```

#### Set timezone

```shell
# Verify time zone:
timedatectl

# Set if incorrect:
sudo timedatectl set-timezone America/Chicago
```

#### Run system updates

```shell
sudo apt update
sudo apt -y dist-upgrade
sudo apt -y autoremove
```

#### Load the w1-gpio and w1_therm modules

These modules are necessary for the getTemps service.

```shell
# Append to /boot/firmware/config.txt:
sudo sh -c "echo 'dtoverlay=w1-gpio' >> /boot/firmware/config.txt"

# Verify entry, dtoverlay=w1-gpio should appear once:
tail /boot/firmware/config.txt

# Verify modules load (no output is good):
sudo modprobe w1-gpio
sudo modprobe w1_therm
```

#### Reboot and verify the modules above load

```shell
sudo reboot
```

```shell
lsmod | grep w1
```


## Ansible Vault

Files like dotenv and some variables are encrypted.  
Do not decrypt .vault files in place. The [.gitignore](../.gitignore) file should ignore .env but not .env.vault  

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


## Ansible inventory file

See [inventory_example.yaml](inventory/inventory_example.yaml)

* getTemps, getPressures, getSHT30, and getWeather are host groups.
* Hosts can be added or removed from each.


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
