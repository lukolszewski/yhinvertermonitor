from modbus2mqtt import *
from modbus2mqtt.autodiscovery import *
from modbus2mqtt.util import *


if __name__ == "__main__":
    if config.get('autodiscovery', {}).get('enabled', 'no') != 'yes':
        logger.info("Autodiscovery is disabled in the config.")
    else:
        for device in config['device']:
            send_autodiscovery(device, config['mqqt_autodiscovery_prefix'],config['mqtt']['broker'], config['mqtt']['port'])

    task_thread = threading.Thread(target=task_runner)
    task_thread.start()
    
    if 'mqtt_write_enable' in config.keys():
        logger.info("MQTT write enabled, starting thread.")
        mqtt_thread = threading.Thread(target=mqtt_listener, args=(config,))
        mqtt_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        shutdown_event.set()
        task_thread.join()
        mqtt_thread.join()
