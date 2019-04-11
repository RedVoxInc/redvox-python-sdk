"""
This module discusses modifying RedVox API 900 files.

Please see the example_packet_writing.py to get an idea of all setters available in this library.

Developer documentation: https://bitbucket.org/redvoxhi/redvox-api900-python-reader/src/master/docs/v1.5.0/redvox-api900-docs.md
API documentation: https://redvoxhi.bitbucket.io/redvox-sdk/v1.5.0/api_docs/redvox
"""

# First, we import the RedVox API 900 reader.
from redvox.api900 import reader

# Next, let's load our example file.
wrapped_packet = reader.read_rdvxz_file("example_data/example.rdvxz")

# We can change any of the top level fields with the associated setter.
print(wrapped_packet.api())
wrapped_packet.set_api(901)
print(wrapped_packet.api())

# We can also set multiple fields at one time.
wrapped_packet.set_api(902).set_authenticated_email("jane.doe@somewhere.com")
print(wrapped_packet.api())
print(wrapped_packet.authenticated_email())

# It's possible to edit sensor sensors as well
print(wrapped_packet.microphone_sensor().sample_rate_hz())
wrapped_packet.microphone_sensor().set_sample_rate_hz(800.0)
print(wrapped_packet.microphone_sensor().sample_rate_hz())

# We can also assign a sensor sensor to a variable and edit it.
barometer_sensor = wrapped_packet.barometer_sensor()
barometer_sensor.set_sensor_name("really_awesome_barometer")
print(wrapped_packet.barometer_sensor().sensor_name())

# Or, we can create a brand new sensor and set it on the packet
light_sensor = reader.LightSensor()
light_sensor \
    .set_sensor_name("really_awesome_light")\
    .set_timestamps_microseconds_utc([4, 5, 6])\
    .set_payload_values([7, 8, 9])
wrapped_packet.set_light_sensor(light_sensor)
print(wrapped_packet.light_sensor())

# Finally, we can also remove a sensor sensor from a packet by passing "None" to the set method.
wrapped_packet.set_gyroscope_sensor(None)
print(wrapped_packet.has_gyroscope_sensor())

