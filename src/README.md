# SandstoneDashboard Python scripts

### Python virtual environment

Activate/deactivate

```shell
source ~/SandstoneDashboard/venv/bin/activate

deactivate
```

Install Python packages from [requirements.txt](../requirements.txt)

```shell
# Make sure the virtual environment is activated.

pip install --upgrade pip  # nice, but not required

pip install -r requirements.txt

pip check  # check for broken requirements
```
