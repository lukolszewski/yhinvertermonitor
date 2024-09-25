from modbus2mqtt import *
from modbus2mqtt.autodiscovery import *
from modbus2mqtt.utility import *

if __name__ == "__main__":
    task_thread = threading.Thread(target=task_runner)
    task_thread.start()
    
    if 'mqtt_write_topic' in config.keys():
        mqtt_thread = threading.Thread(target=mqtt_listener)
        mqtt_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        shutdown_event.set()
        task_thread.join()
        mqtt_thread.join()
