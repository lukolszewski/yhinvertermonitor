import pytest
from unittest.mock import patch, MagicMock
import yaml
from modbus2mqtt.util import read_register, write_register, swap_list_bytes, divide, perform_task
import random

# Load original configuration from the YAML file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Assuming `config['device'][0]` contains the device we're testing
device = config['device'][0]

# Extract registers mapping for testing
registers = {reg['id']: reg for reg in device['registers']}


class TestModbusUtil:

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        # Patch the Instrument creation in minimalmodbus to prevent it from opening a real port
        self.mock_instrument = MagicMock()
        patcher = patch('modbus2mqtt.util.minimalmodbus.Instrument', return_value=self.mock_instrument)
        patcher.start()

        # Set mock behaviors for read and write
        self.mock_instrument.read_register = MagicMock(return_value=0x1234)  # Example register value for testing
        self.mock_instrument.write_register = MagicMock()

        # Patch the config to be available globally in the `modbus2mqtt` package
        patch('modbus2mqtt.config', config).start()
        # Patch the `instrument` to use the mocked one
        patch('modbus2mqtt.util.instrument', self.mock_instrument).start()

        # Patch the MQTT publish function
        self.mock_mqtt_publish = patch('modbus2mqtt.util.publish.multiple').start()

        yield

        # Teardown: Stop all patches after each test
        patch.stopall()

    @pytest.fixture
    def mock_queue(self):
        # Create a mock queue to simulate write tasks
        queue = MagicMock()
        # Simulate a single write task in the queue
        queue.get = MagicMock(side_effect=[
            {'register': 4501, 'value': 123, 'write_enable': True},
        ])
        # Simulate that the queue has one task, then becomes empty
        queue.empty = MagicMock(side_effect=[False, True])
        return queue

    def test_swap_list_bytes(self):
        # Define a test case with known input and expected output
        input_list = [0x1234, 0xABCD, 0x0000, 0xFFFF]  # Example 16-bit integers
        expected_output = [0x3412, 0xCDAB, 0x0000, 0xFFFF]  # Expected byte-swapped output

        # Call the function with the test input
        result = swap_list_bytes(input_list)

        # Assert that the result matches the expected output
        assert result == expected_output

    def test_swap_empty_list(self):
        # Test with an empty list input
        input_list = []
        expected_output = []

        result = swap_list_bytes(input_list)

        assert result == expected_output

    def test_swap_single_value(self):
        # Test with a single value in the list
        input_list = [0x1234]
        expected_output = [0x3412]

        result = swap_list_bytes(input_list)

        assert result == expected_output

    @pytest.mark.parametrize(
        "swap, reg",
        [
            (True, 4501),  # `reg` has reg_info and swap=True
            (False, 4501),  # `reg` has reg_info and swap=False
            (True, 9999),  # `reg` does not have reg_info and swap=True
            (False, 9999),  # `reg` does not have reg_info and swap=False
        ]
    )
    def test_read_register(self, swap, reg):
        val = 0x1234

        # Perform the read operation
        msgs = read_register(reg, self.mock_instrument, registers, config, swap=swap)

        # Validate the generated messages
        assert isinstance(msgs, list)
        for msg in msgs:
            assert 'topic' in msg
            assert 'payload' in msg

            # Compute the expected value considering swap and transformation
            expected_value = val
            if swap:
                expected_value = swap_list_bytes([val])[0]

            reg_info = registers.get(reg, [])
            if reg_info:
                transform_function = globals()[reg_info['transform']]
                expected_value = transform_function(expected_value, reg_info['argument'])
                expected_value = round(expected_value, reg_info['rounding'])
            else:
                transform_function = globals()[config.get('default_transform', 'divide')]
                expected_value = transform_function(expected_value, config.get('default_argument', 1))
                expected_value = round(expected_value, config.get('default_rounding', 0))

            assert msg['payload'] == str(expected_value)

    def test_write_register(self):
        # Test writing to a Modbus register
        register_to_write = 4501
        value_to_write = 123
        write_register(register_to_write, value_to_write, self.mock_instrument)

        # Validate the write action
        self.mock_instrument.write_register.assert_called_once_with(register_to_write, value_to_write, 0, 6, False)

    def test_perform_task(self, mock_queue):
        return_values=[random.randrange(0,65535,1) for a in range(0,device['read']['number_of_registers'])]
        # Configure the mock instrument for reading and writing operations
        self.mock_instrument.read_registers = MagicMock(return_value=return_values)  # Example register values

        # Run the perform_task function with the mocked setup
        perform_task(config, device, mock_queue)

        # Validate that `write_register` was called once
        self.mock_instrument.write_register.assert_called_once_with(4501, 123, 0, 6, False)

        # Validate that `read_registers` was called once with correct parameters
        self.mock_instrument.read_registers.assert_called_once_with(device['read']['start_register'], device['read']['number_of_registers'])

        # Validate that messages were published via MQTT
        self.mock_mqtt_publish.assert_called_once()
        msgs = self.mock_mqtt_publish.call_args[0][0]  # Extract the list of messages

        # Validate that the messages are in the expected format
        assert isinstance(msgs, list)
        assert len(msgs) > 0  # Ensure at least one message was published

        # Further checks can validate that the messages are correctly formed
        for msg in msgs:
            assert 'topic' in msg
            assert 'payload' in msg
            print(msg)  # For debugging purposes
