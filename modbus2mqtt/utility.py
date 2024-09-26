from modbus2mqtt import *

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

        # Check the queue for any write operations
        while not write_queue.empty():
            write_task = write_queue.get()
            if write_task['write_enable']:
                logger.info("Executing write")
                write_register(write_task['register'], write_task['value'])
                time.sleep(1)

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
        #print(msgs)
        publish.multiple(msgs, hostname=mqtt_broker, port=mqtt_port, protocol=MQTTProtocolVersion.MQTTv5)
        logger.info("All messages published successfully.")
    except Exception as e:
        logger.error(f"Failed to read from device or process data: {e}")
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8').split(',')
        register = int(payload[0])
        value = int(payload[1])
        write_enable = payload[2].lower() == 'true'
        logger.info("Got incoming write message for register:"+str(register)+", value:"+str(value)+", write:"+str(write_enable))
        write_queue.put({'register': register, 'value': value, 'write_enable': write_enable})
    except Exception as e:
        logger.error(f"Error processing incoming MQTT message: {e}")

def mqtt_listener():
    mqtt_broker = config['mqtt']['broker']
    mqtt_port = config['mqtt']['port']
    mqtt_topic = config['mqtt_write_topic']
    logger.info("MQQT write listener starting")
    client = mqtt.Client()
    client.on_message = on_message

    client.connect(mqtt_broker, mqtt_port, 60)
    client.subscribe(mqtt_topic)

    client.loop_start()
    shutdown_event.wait()
    client.loop_stop()

def task_runner():
    while not shutdown_event.is_set():
        perform_task()
        time.sleep(1)