from modbus2mqtt import *
from modbus2mqtt.autodiscovery import *


if __name__ == "__main__":
    if config.get('autodiscovery', {}).get('enabled', 'no') != 'yes':
        logger.info("Autodiscovery is disabled in the config.")
        exit(0)

    for device in config['device']:
        send_autodiscovery(device, config['mqqt_autodiscovery_prefix'],config['mqtt']['broker'], config['mqtt']['port'])
