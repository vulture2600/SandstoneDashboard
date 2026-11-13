# Bash

![bash1](../../images_diagrams/bash1.png)
![bash2](../../images_diagrams/bash2.png)

The default .bashrc file sources .bash_aliases, but not .bash_functions  
The Ansible playbook manages the block to source .bash_fuctions  
Verify both blocks are present and not duplicated .bashrc

```shell
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
```

```shell
if [ -f ~/.bash_functions ]; then
    . ~/.bash_functions
fi
```
