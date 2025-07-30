# Ansible

#### Manage the Raspberry Pi's

Preflight checks

```shell
ansible-lint systemd_playbook.yml  # lint check

ansible-playbook systemd_playbook.yml --syntax-check  # check for syntax errors

# Dry run, show what will change, only hosts in the monitors group in inventory.ini:
ansible-playbook systemd_playbook.yml -i inventory.ini -l monitors --diff --check
```

Run the playbook

```shell
# Run the playbook against the monitors group in inventory.ini (add --diff to see changes):
ansible-playbook systemd_playbook.yml -i inventory.ini -l monitors
```

#### Ansible inventory file example

inventory.ini

```ini
[monitors]
HOSTNAME ansible_host=FQDN_HOSTNAME ansible_user=SSH_USER ansible_port=PORT
```
