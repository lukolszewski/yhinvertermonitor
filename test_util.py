import unittest
from unittest.mock import patch, MagicMock
import yaml
import json

# Import functions from the updated `util.py` in the `modbus2mqtt` package
from modbus2mqtt.util import read_register, write_register, swap_list_bytes, divide

class TestModbusUtilSingleRegister(unittest.TestCase):

    def setUp(self):
        # Load config from config.yaml
        with open('config.yaml', 'r') as file:
            self.config = yaml.safe_load(file)

        # Assuming `config['device'][0]` contains the device we're testing
        self.device = self.config['device'][0]

        # Extract serial configuration
        self.serial_config = self.config['serial']

        # Extract registers mapping for testing
        self.registers = {reg['id']: reg for reg in self.device['registers']}

        # Patch the Instrument creation in minimalmodbus to prevent it from opening a real port
        self.mock_instrument = MagicMock()
        patcher = patch('modbus2mqtt.util.minimalmodbus.Instrument', return_value=self.mock_instrument)
        self.addCleanup(patcher.stop)
        patcher.start()

        # Set mock behaviors for read and write
        self.mock_instrument.read_register = MagicMock(return_value=0x1234)  # Example register value for testing
        self.mock_instrument.write_register = MagicMock()

        # Patch the config to be available globally in the `modbus2mqtt` package
        patch('modbus2mqtt.config', self.config).start()
        # Patch the `instrument` to use the mocked one
        patch('modbus2mqtt.util.instrument', self.mock_instrument).start()

    def test_swap_list_bytes(self):
        # Define a test case with known input and expected output
        input_list = [0x1234, 0xABCD, 0x0000, 0xFFFF]  # Example 16-bit integers
        expected_output = [0x3412, 0xCDAB, 0x0000, 0xFFFF]  # Expected byte-swapped output

        # Call the function with the test input
        result = swap_list_bytes(input_list)

        # Assert that the result matches the expected output
        self.assertEqual(result, expected_output)

    def test_swap_empty_list(self):
        # Test with an empty list input
        input_list = []
        expected_output = []

        result = swap_list_bytes(input_list)

        self.assertEqual(result, expected_output)

    def test_swap_single_value(self):
        # Test with a single value in the list
        input_list = [0x1234]
        expected_output = [0x3412]

        result = swap_list_bytes(input_list)

        self.assertEqual(result, expected_output)

    def test_read_register(self):
        val = 0x1234
        reg = 4501
        swap = True
        self.mock_instrument.read_register = MagicMock(return_value=val)
        # Test reading a single register and ensure correct message is created
        msgs = read_register(reg, self.mock_instrument, self.registers, self.config, swap = swap)
        
        # Validate the generated messages
        self.assertTrue(isinstance(msgs, list))
        for msg in msgs:
            self.assertIn('topic', msg)
            self.assertIn('payload', msg)
            if swap:
                expected_value = swap_list_bytes([val])[0]
            reg_info = self.registers.get(reg)
            if reg_info:
                transform_function = globals()[reg_info['transform']]
                expected_value = transform_function(expected_value, reg_info['argument'])
                expected_value = round(expected_value, reg_info['rounding'])

            self.assertEqual(msg['payload'],str(expected_value))
            print(msg)

    def test_write_register(self):
        # Test writing to a Modbus register
        register_to_write = 4501
        value_to_write = 123
        write_register(register_to_write, value_to_write, self.mock_instrument)

        # Validate the write action
        self.mock_instrument.write_register.assert_called_once_with(register_to_write, value_to_write, 0, 6, False)

    def tearDown(self):
        # Stop all patches after each test
        patch.stopall()

if __name__ == '__main__':
    unittest.main()
