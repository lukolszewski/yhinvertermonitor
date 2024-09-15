import yaml
import minimalmodbus
import paho.mqtt.publish as publish
from paho.mqtt.enums import MQTTProtocolVersion
import time
import logging
import logging.handlers
import threading
import os
import traceback

# Initialize global variables and locks
lock = threading.Lock()
shutdown_event = threading.Event()
instrument=None

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

# Registers configuration
registers = {reg['id']: reg for reg in config['registers']}
# MQQT Config
mqtt_prefix=config.get('mqtt_prefix','')
if mqtt_prefix:
    mqtt_prefix = mqtt_prefix+'/'

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

def swap_list_bytes(int_list):
    swapped_ints = []
    for value in int_list:
        value = value & 0xFFFF  # Ensure it is a 16-bit unsigned number
        swapped = ((value >> 8) & 0xFF) | ((value & 0xFF) << 8)
        swapped_ints.append(swapped)
    return swapped_ints

def divide(x, y):
    return x / y if y != 0 else 0

def setup_instrument():
    global instrument
    device = config['serial']['device']
    baudrate = config['serial']['baudrate']
    timeout = config['serial']['timeout']
    slave_id = config['serial']['slave_id']
    mode = config['serial']['mode']
    instrument = minimalmodbus.Instrument(device, slave_id, mode=mode)
    instrument.serial.baudrate = baudrate
    instrument.serial.timeout = timeout

def read_seq_registers(start,number):
    if instrument is None or start is None or number is None:
        raise Exception("Bad arguments given to read_seq_registers")
    values = instrument.read_registers(start, number)
    values = swap_list_bytes(values)
    # Collect all messages to publish
    msgs = []
    for register in range(start, start + number):
        value = values[register - start]
        reg_info = registers.get(register)
        if reg_info:
            transform_function = globals()[reg_info['transform']]
            transformed_value = transform_function(value, reg_info['argument'])
            rounded_value = round(transformed_value, reg_info['rounding'])
            message = {
                'topic': mqtt_prefix+reg_info['topic'],
                'payload': f"{rounded_value}"
            }
            msgs.append(message)
        elif config.get('push_unknown_registers','no') == 'yes':
            transform_function = globals()[config.get('default_transform','divide')]
            transformed_value = transform_function(value, config.get('default_argument',1))
            rounded_value = round(transformed_value, config.get('default_rounding',0))
            message = {
                'topic': mqtt_prefix+"register"+str(register),
                'payload': f"{rounded_value}"
            }
            msgs.append(message)
    return msgs

def read_register(number):
    if instrument is None or number is None:
        raise Exception("Bad arguments given to read_register")

    value = instrument.read_register(number)
    value = swap_list_bytes([value])[0]
    reg_info = registers.get(number)
    msgs = []
    if reg_info:
        transform_function = globals()[reg_info['transform']]
        transformed_value = transform_function(value, reg_info['argument'])
        rounded_value = round(transformed_value, reg_info['rounding'])
        message = {
            'topic': mqtt_prefix+reg_info['topic'],
            'payload': f"{rounded_value}"
        }
        msgs.append(message)
    elif config.get('push_unknown_registers','no') == 'yes':
        transform_function = globals()[config.get('default_transform','divide')]
        transformed_value = transform_function(value, config.get('default_argument',1))
        rounded_value = round(transformed_value, config.get('default_rounding',0))
        message = {
            'topic': mqtt_prefix+"register"+str(number),
            'payload': f"{rounded_value}"
        }
        msgs.append(message)
    return msgs

def write_register(number,value):
    if instrument is None or number is None or value is None:
        raise Exception("Bad arguments given to write_register")
    instrument.write_register(number,value,0,6,False)

def perform_task():
    try:
        # MQTT configuration
        mqtt_broker = config['mqtt']['broker']
        mqtt_port = config['mqtt']['port']

        setup_instrument()

        # Read and process seq registers
        start_register = config['read']['start_register']
        number_of_registers = config['read']['number_of_registers']
        
        msgs = []
        if number_of_registers is not None and number_of_registers > 0:
            msgs.extend(read_seq_registers(start_register,number_of_registers))

        read_single=config.get('read_single',[])
        for rs in read_single:
            msgs.extend(read_register(rs))

        # Publish all messages in one call
        print(msgs)
        publish.multiple(msgs, hostname=mqtt_broker, port=mqtt_port, protocol=MQTTProtocolVersion.MQTTv5)
        logger.info("All messages published successfully.")
    except Exception as e:
        logger.error(f"Failed to read from device or process data: {e}")
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())

def task_runner():
    while not shutdown_event.is_set():
        perform_task()
        time.sleep(1)

if __name__ == "__main__":
    task_thread = threading.Thread(target=task_runner)
    task_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        shutdown_event.set()
        task_thread.join()