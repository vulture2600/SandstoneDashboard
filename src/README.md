# SandstoneDashboard Python scripts

### Python virtual environment

Activate/deactivate

```shell
# If the directory has a .venv symlink, try using the 'activate' alias instead of the source command.

cd ~/SandstoneDashboard  # or any directory with a venv
source venv/bin/activate

deactivate
```

Install Python packages from [requirements.txt](../requirements.txt)

```shell
# Make sure the virtual environment is activated.

pip install --upgrade pip setuptools  # nice, but not required

pip install -r requirements.txt

pip check  # check for broken requirements
```

### Logging

```shell
tail -f /var/log/getPressures.log
tail -f /var/log/getSHT30.log
tail -f /var/log/getTemps.log
tail -f /var/log/getWeather.log
```
