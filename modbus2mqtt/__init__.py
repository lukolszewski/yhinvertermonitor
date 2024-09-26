import yaml
import json
import minimalmodbus
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
from paho.mqtt.enums import MQTTProtocolVersion
import time
import logging
import logging.handlers
import threading
import queue
import os
import traceback

# Initialize global variables and locks
lock = threading.Lock()
shutdown_event = threading.Event()
instrument=None
write_queue = queue.Queue()
write_queues = []

# Define the path to the config file
config_file_path = 'config.yaml'

# Check if the config file exists
if not os.path.exists(config_file_path):
    print(f"Error: The configuration file {config_file_path} was not found.")
    exit(1)  # Exit if the config file does not exist

# Load configuration from YAML file
with open(config_file_path, 'r') as file:
    config = yaml.safe_load(file)

if config is None:
    print("Error: Configuration is empty or incorrectly formatted.")
    exit(1)  # Exit if the configuration is not loaded properly

def setup_logging():
    log_filename = config.get('logpath', 'app.log')
    log_file_size_limit = config.get('log_file_size_limit', 1048576)  # Use a default value if not specified

    # Ensure the log directory exists
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)

    # Set up a logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=log_file_size_limit, backupCount=5)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger

logger = setup_logging()

for device in config['device']:
    write_queues.append(queue.Queue())


# MQQT Config
mqtt_prefix=config.get('mqtt_prefix','')
if mqtt_prefix:
    mqtt_prefix = mqtt_prefix+'/'

