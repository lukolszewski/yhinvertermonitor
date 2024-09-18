import yaml
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

# Registers configuration
registers = {reg['id']: reg for reg in config['registers']}
# MQQT Config
mqtt_prefix=config.get('mqtt_prefix','')
if mqtt_prefix:
    mqtt_prefix = mqtt_prefix+'/'


def clear_autodiscovery():
    try:
        if config.get('autodiscovery', {}).get('enabled', 'no') != 'yes':
            logger.info("Autodiscovery is disabled in the config.")
            return

        # Device-specific information from the config
        device_info = config.get('autodiscovery', {}).get('device', {})
        device_identifier = device_info.get('identifiers', [])
        device_identifier = [identifier.lower() for identifier in device_identifier]  # Ensure it's lowercase

        discovery_prefix = config.get('mqqt_autodiscovery_prefix', None)
        if not discovery_prefix:
            logger.error("Autodiscovery prefix is not configured.")
            return
        
        mqtt_broker = config.get('mqtt', {}).get('broker')
        mqtt_port = config.get('mqtt', {}).get('port')

        if not mqtt_broker or not mqtt_port:
            logger.error("MQTT broker or port is not configured.")
            return

        messages = []  # List to store all messages for clearing autodiscovery

        # Iterate over all registers
        for reg in config.get('registers', []):
            # Skip if register has 'noautodiscovery' key
            if reg.get('noautodiscovery', False):
                logger.info(f"Skipping clearing autodiscovery for register {reg['id']} due to 'noautodiscovery' flag.")
                continue

            register_id = reg.get('id')
            topic = reg.get('topic')

            if not register_id or not topic:
                logger.error(f"Register with missing 'id' or 'topic': {reg}")
                continue  # Skip this register if mandatory fields are missing

            object_id = f"register{register_id}"

            # Autodiscovery topic format: {discovery_prefix}/sensor/{device_identifier[0]}/register{register_id}/config
            autodiscovery_topic = f"{discovery_prefix}/sensor/{device_identifier[0]}/register{register_id}/config"

            # Prepare the message for MQTT with an empty payload, no retain flag
            message = {
                "topic": autodiscovery_topic,
                "payload": "",  # Empty payload to clear retained message
                "retain": False,  # Do not retain the empty message, just clear the retained one
                "qos": 1  # Ensure at least once delivery
            }

            # Append the message to the list
            messages.append(message)

        # Publish all clear autodiscovery messages in one go
        if messages:
            publish.multiple(messages, hostname=mqtt_broker, port=mqtt_port, protocol=MQTTProtocolVersion.MQTTv5)
            logger.info(f"Cleared {len(messages)} retained autodiscovery messages.")
        else:
            logger.warning("No autodiscovery messages were found to clear.")
    except Exception as e:
        logger.error(f"Error during clearing autodiscovery messages: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    clear_autodiscovery()