"""
test file to read all 1-wire temp folders and post their current temps to database



"""



import os
import time
import datetime
from os import path
import threading
from constants import DEVICES_PATH, W1_SLAVE_FILE



