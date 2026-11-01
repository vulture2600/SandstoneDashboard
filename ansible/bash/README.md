# Bash

This is not currently deployed by Ansible.  
Add or uncomment the following blocks in .bashrc

```shell
if [ -f ~/.bash_functions ]; then
    . ~/.bash_functions
fi
```

```shell
if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi
```

Copy [.bash_functions](.bash_functions) to ```~/.bash_functions```  
Copy [.bash_aliases](.bash_aliases) to ```~/.bash_aliases```  
Cop [.ascii_nomic.txt](.ascii_nomic.txt) to ```~/.ascii_nomic.txt```  
Copy [motd](motd) to ```/etc/motd```
