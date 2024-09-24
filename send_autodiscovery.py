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

import json

def send_autodiscovery():
    try:
        if config.get('autodiscovery', {}).get('enabled', 'no') != 'yes':
            logger.info("Autodiscovery is disabled in the config.")
            return

        device_info = config.get('autodiscovery', {}).get('device', {})
        device_identifier = device_info.get('identifiers', [])
        device_identifier = [identifier.lower() for identifier in device_identifier]

        if not device_identifier:
            logger.error("Device identifier is missing in autodiscovery configuration.")
            return

        discovery_prefix = config.get('mqqt_autodiscovery_prefix', None)
        if not discovery_prefix:
            logger.error("Autodiscovery prefix is not configured.")
            return
        
        mqtt_broker = config.get('mqtt', {}).get('broker')
        mqtt_port = config.get('mqtt', {}).get('port')

        if not mqtt_broker or not mqtt_port:
            logger.error("MQTT broker or port is not configured.")
            return

        messages = []

        ignored_register_keys = {'id', 'topic', 'transform', 'argument', 'rounding', 'name', 'noautodiscovery'}

        # Process registers
        for reg in config.get('registers', []):
            if reg.get('noautodiscovery', False):
                logger.info(f"Skipping autodiscovery for register {reg.get('id', 'unknown')} due to 'noautodiscovery' flag.")
                continue

            register_id = reg.get('id')
            topic = reg.get('topic')

            if not register_id or not topic:
                logger.error(f"Register with missing 'id' or 'topic': {reg}")
                continue

            object_id = f"register{register_id}"
            register_name = reg.get('name', f"Register {register_id}")
            unique_id = f"{device_identifier[0]}_{topic}" if device_identifier else f"register_{register_id}"
            state_topic = f"{mqtt_prefix}{topic}"

            message_payload = {
                "name": register_name,
                "state_topic": state_topic,
                "unique_id": unique_id
            }

            if device_info:
                message_payload["device"] = {key: value for key, value in device_info.items()}

            for key, value in reg.items():
                if key not in ignored_register_keys:
                    message_payload[key] = value

            autodiscovery_topic = f"{discovery_prefix}/sensor/{device_identifier[0]}/register{register_id}/config"
            message = {
                "topic": autodiscovery_topic,
                "payload": json.dumps(message_payload),
                "retain": True,
                "qos": 1
            }
            messages.append(message)

        # Process extra entities
        extra_entities = config.get('autodiscovery', {}).get('extra', {})
        if not isinstance(extra_entities, dict):
            logger.error("Extra entities configuration is not a dictionary.")
            return

        for entity_category, entities in extra_entities.items():
            if not isinstance(entities, list):
                logger.error(f"Entities under category {entity_category} are not a list.")
                continue

            for entity in entities:
                if entity.get('noautodiscovery', False):
                    continue

                entity_id = entity.get('id')
                entity_payload = {k: v for k, v in entity.items() if k != 'id'}
                unique_id = f"{device_identifier[0]}_{entity_category}{entity_id}" if entity_id else f"{entity_category}_{device_identifier[0]}"
                entity_payload["unique_id"] = unique_id

                if device_info:
                    entity_payload["device"] = {key: value for key, value in device_info.items()}

                autodiscovery_topic = f"{discovery_prefix}/{entity_category}/{device_identifier[0]}/{entity_category}{entity_id}/config"
                message = {
                    "topic": autodiscovery_topic,
                    "payload": json.dumps(entity_payload),
                    "retain": True,
                    "qos": 1
                }
                messages.append(message)

        if messages:
            publish.multiple(messages, hostname=mqtt_broker, port=mqtt_port, protocol=MQTTProtocolVersion.MQTTv5)
            logger.info(f"Sent {len(messages)} autodiscovery messages with retain and QoS 1.")
        else:
            logger.warning("No autodiscovery messages were prepared.")
    except Exception as e:
        logger.error(f"Error during autodiscovery process: {e}")
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    send_autodiscovery()
