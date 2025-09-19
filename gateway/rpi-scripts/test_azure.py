import os
from azure.iot.device import IoTHubDeviceClient, Message

conn_str = os.getenv("IOTHUB_DEVICE_CONNECTION_STRING")
client = IoTHubDeviceClient.create_from_connection_string(conn_str)

client.connect()
message = Message("Test message from Raspberry Pi")
client.send_message(message)
print("Message successfully sent to Azure IoT Hub")
client.disconnect()
