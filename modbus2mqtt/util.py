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

def setup_instrument(device,baudrate,timeout,slave_id,mode):
    instrument = minimalmodbus.Instrument(device, slave_id, mode=mode)
    instrument.serial.baudrate = baudrate
    instrument.serial.timeout = timeout
    return instrument

def read_seq_registers(start,number,instrument,registers,config, swap = True):
    if instrument is None or start is None or number is None:
        raise Exception("Bad arguments given to read_seq_registers")
    values = instrument.read_registers(start, number)
    if swap:
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

def read_register(number, instrument,registers,config,swap=True):
    if instrument is None or number is None:
        raise Exception("Bad arguments given to read_register")

    value = instrument.read_register(number)
    if swap:
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

def write_register(number,value, instrument):
    if instrument is None or number is None or value is None:
        raise Exception("Bad arguments given to write_register")
    instrument.write_register(number,value,0,6,False)

def perform_task(config,device,write_queue):
    try:
        # MQTT configuration
        mqtt_broker = config['mqtt']['broker']
        mqtt_port = config['mqtt']['port']

        instrument = setup_instrument(config['serial']['device'],
                                        config['serial']['baudrate'],
                                        device['timeout'],
                                        device['slave_id'],
                                        device['mode'])
        
        registers = {reg['id']: reg for reg in device['registers']}

        # Check the queue for any write operations
        while not write_queue.empty():
            write_task = write_queue.get()
            if write_task['write_enable']:
                logger.info("Executing write")
                write_register(write_task['register'], write_task['value'],instrument)
                time.sleep(1)

        # Read and process seq registers
        start_register = device['read']['start_register']
        number_of_registers = device['read']['number_of_registers']
        if device.get('swap_byteorder_on_receive','yes') == 'yes':
            swap = True
        else:
            swap = False
        
        msgs = []
        if number_of_registers is not None and number_of_registers > 0:
            msgs.extend(read_seq_registers(start_register, number_of_registers, instrument, registers, config, swap = swap))

        read_single=device.get('read_single',[])
        for rs in read_single:
            msgs.extend(read_register(rs, instrument, registers, config, swap = swap))

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
        global write_queues
        global config
        topic = msg.topic
        mqtt_topics = []
        queue_no = None
        for device in config['device']:
            mqtt_topic = device['mqtt_prefix']+'/'+device['mqtt_write_topic']
            mqtt_topics.append(mqtt_topic)
        for index,device_topic in enumerate(mqtt_topics):
            if topic == device_topic:
                queue_no = index
        if queue_no is None:
            logger.error(f"Error processing incoming MQTT message: {e}")
            return
        payload = msg.payload.decode('utf-8').split(',')
        register = int(payload[0])
        value = int(payload[1])
        write_enable = payload[2].lower() == 'true'
        logger.info("Got incoming write message for register:"+str(register)+", value:"+str(value)+", write:"+str(write_enable))
        write_queues[queue_no].put({'register': register, 'value': value, 'write_enable': write_enable})
    except Exception as e:
        logger.error(f"Error processing incoming MQTT message: {e}")

def mqtt_listener(config):
    mqtt_broker = config['mqtt']['broker']
    mqtt_port = config['mqtt']['port']

    mqtt_topics = []
    for device in config['device']:
        mqtt_topic = device['mqtt_prefix']+'/'+device['mqtt_write_topic']
        mqtt_topics.append(mqtt_topic)
        logger.info("MQQT write listener for device " +str(device['slave_id'])+ " adding")
    
    client = mqtt.Client()
    client.on_message = on_message

    client.connect(mqtt_broker, mqtt_port, 60)
    client.subscribe([(topic, 0) for topic in mqtt_topics])

    client.loop_start()
    shutdown_event.wait()
    client.loop_stop()

def task_runner():
    while not shutdown_event.is_set():
        for index,device in enumerate(config['device']):
            perform_task(config, device, write_queues[index])

        time.sleep(1)