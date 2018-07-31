from redvox.api900 import reader
from tests.test_utils import ArraysTestCase
import tests.mock_packets

import unittest

from redvox.api900.lib import api900_pb2


class TestWrappedRedvoxPacket(unittest.TestCase):
    def setUp(self):
        self.base_packet: api900_pb2.RedvoxPacket = tests.mock_packets.base_packet()
        self.wrapped_synthetic_packet = reader.wrap(self.base_packet)
        self.wrapped_example_packet = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))

    def test_api(self):
        self.assertEqual(self.wrapped_synthetic_packet.api(), 900)
        self.assertEqual(self.wrapped_example_packet.api(), 900)

    def test_redvox_id(self):
        self.assertEqual(self.wrapped_synthetic_packet.redvox_id(), "1")
        self.assertEqual(self.wrapped_example_packet.redvox_id(), "0000001314")

    def test_uuid(self):
        self.assertEqual(self.wrapped_synthetic_packet.uuid(), "2")
        self.assertEqual(self.wrapped_example_packet.uuid(), "317985785")

    def test_authenticated_email(self):
        self.assertEqual(self.wrapped_synthetic_packet.authenticated_email(), "foo@bar.baz")
        self.assertEqual(self.wrapped_example_packet.authenticated_email(), "anthony.christe@gmail.com")

    def test_authentication_token(self):
        self.assertEqual(self.wrapped_synthetic_packet.authentication_token(), "test_authentication_token")
        self.assertEqual(self.wrapped_example_packet.authentication_token(), "redacted-1005665114")

    def test_firebase_token(self):
        self.assertEqual(self.wrapped_synthetic_packet.firebase_token(), "test_firebase_token")
        self.assertEqual(self.wrapped_example_packet.firebase_token(),
                         "eCCYsQxSRCE:APA91bG_RPDPvr-ALh8taZp6sBYVM1ehORnXrhG5PTOVR-KuYIf1dygYgaXEWNMKtXtqzQCyP0tkBwNmTjyvCCZSKwy-hVjWm3NKwgE-DtJdvMOMaw5Jb0DS3_NXnVnuVXrzjixMjAnvecFFagXYSBwKv5LUtMWpBw")

    def test_is_backfilled(self):
        self.assertFalse(self.wrapped_synthetic_packet.is_backfilled())
        self.assertTrue(self.wrapped_example_packet.is_backfilled())

    def test_is_private(self):
        self.assertTrue(self.wrapped_synthetic_packet.is_private())
        self.assertFalse(self.wrapped_example_packet.is_private())

    def test_is_scrambled(self):
        self.assertTrue(self.wrapped_synthetic_packet.is_scrambled())
        self.assertFalse(self.wrapped_example_packet.is_scrambled())

    def test_device_make(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_make(), "test device make")
        self.assertEqual(self.wrapped_example_packet.device_make(), "Google")

    def test_device_model(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_model(), "test device model")
        self.assertEqual(self.wrapped_example_packet.device_model(), "Pixel XL")

    def test_device_os(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_os(), "test device os")
        self.assertEqual(self.wrapped_example_packet.device_os(), "Android")

    def test_device_os_version(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_os_version(), "test device os version")
        self.assertEqual(self.wrapped_example_packet.device_os_version(), "8.1.0")

    def test_app_version(self):
        self.assertEqual(self.wrapped_synthetic_packet.app_version(), "test app version")
        self.assertEqual(self.wrapped_example_packet.app_version(), "2.3.4")

    def test_battery_level_percent(self):
        self.assertEqual(self.wrapped_synthetic_packet.battery_level_percent(), 99.0)
        self.assertEqual(self.wrapped_example_packet.battery_level_percent(), 25.0)

    def test_device_temperature_c(self):
        self.assertEqual(self.wrapped_synthetic_packet.device_temperature_c(), 25.0)
        self.assertEqual(self.wrapped_example_packet.device_temperature_c(), 32.0)

    def test_acquisition_server(self):
        self.assertEqual(self.wrapped_synthetic_packet.acquisition_server(), "test acquisition server")
        self.assertEqual(self.wrapped_example_packet.acquisition_server(),
                         "wss://milton.soest.hawaii.edu:8000/acquisition/v900")

    def test_time_synchronization_server(self):
        self.assertEqual(self.wrapped_synthetic_packet.time_synchronization_server(),
                         "test time synchronization server")
        self.assertEqual(self.wrapped_example_packet.time_synchronization_server(), "wss://redvox.io/synch/v2")

    def test_authentication_server(self):
        self.assertEqual(self.wrapped_synthetic_packet.authentication_server(), "test authentication server")
        self.assertEqual(self.wrapped_example_packet.authentication_server(), "https://redvox.io/login/mobile")

    def test_app_file_start_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(self.wrapped_synthetic_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                         1519166348000000)
        self.assertEqual(self.wrapped_example_packet.app_file_start_timestamp_epoch_microseconds_utc(),
                         1532656864354000)

    def test_app_file_start_timestamp_machine(self):
        self.assertEqual(self.wrapped_synthetic_packet.app_file_start_timestamp_machine(), 42)
        self.assertEqual(self.wrapped_example_packet.app_file_start_timestamp_machine(), 1532656848035001)

    def test_server_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(self.wrapped_synthetic_packet.server_timestamp_epoch_microseconds_utc(),
                         1519166348000000 + 10000)
        self.assertEqual(self.wrapped_example_packet.server_timestamp_epoch_microseconds_utc(), 1532656543460000)

    def test_metadata(self):
        self.assertTrue("foo" in self.wrapped_synthetic_packet.metadata_as_dict())
        self.assertEqual(self.wrapped_synthetic_packet.metadata_as_dict()["foo"], "bar")


class TestEvenlySampledSensor(unittest.TestCase):
    def setUp(self):
        self.base_packet: api900_pb2.RedvoxPacket = tests.mock_packets.simple_mic_packet()
        self.wrapped_synthetic_packet = reader.wrap(self.base_packet)
        self.wrapped_example_packet = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))
        self.synthetic_microphone_channel = self.wrapped_synthetic_packet.microphone_channel()
        self.example_microphone_channel = self.wrapped_example_packet.microphone_channel()

    def test_contains_evenly_sampled_channel(self):
        self.assertTrue(api900_pb2.MICROPHONE in self.synthetic_microphone_channel.evenly_sampled_channel.channel_types)
        self.assertTrue(api900_pb2.MICROPHONE in self.example_microphone_channel.evenly_sampled_channel.channel_types)

    def test_sensor_name(self):
        self.assertEqual(self.synthetic_microphone_channel.sensor_name(), "test microphone sensor name")
        self.assertEqual(self.example_microphone_channel.sensor_name(), "I/INTERNAL MIC")

    def test_sample_rate_hz(self):
        self.assertEqual(self.synthetic_microphone_channel.sample_rate_hz(), 80.0)
        self.assertEqual(self.example_microphone_channel.sample_rate_hz(), 80.0)

    def test_first_sample_timestamp_epoch_microseconds_utc(self):
        self.assertEqual(self.synthetic_microphone_channel.first_sample_timestamp_epoch_microseconds_utc(),
                         1519166348000000)
        self.assertEqual(self.example_microphone_channel.first_sample_timestamp_epoch_microseconds_utc(),
                         1532656864354000)

    def test_metadata_as_dict(self):
        synthetic_dict = self.synthetic_microphone_channel.metadata_as_dict()
        self.assertEqual(len(synthetic_dict), 2)
        self.assertTrue("a" in synthetic_dict and "c" in synthetic_dict)
        self.assertEqual(synthetic_dict["a"], "b")
        self.assertEqual(synthetic_dict["c"], "d")
        self.assertEqual(len(self.example_microphone_channel.metadata_as_dict()), 0)


class TestUnevenlySampledSensor(ArraysTestCase):
    def setUp(self):
        self.base_packet: api900_pb2.RedvoxPacket = tests.mock_packets.simple_bar_packet()
        self.wrapped_synthetic_packet = reader.wrap(self.base_packet)
        self.wrapped_example_packet = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))
        self.synthetic_barometer_channel = self.wrapped_synthetic_packet.barometer_channel()
        self.example_barometer_channel = self.wrapped_example_packet.barometer_channel()

    def test_sensor_name(self):
        self.assertEqual(self.synthetic_barometer_channel.sensor_name(), "test barometer sensor name")
        self.assertEqual(self.example_barometer_channel.sensor_name(), "BMP285 pressure")

    def test_timestamps_microseconds_utc(self):
        self.assertArraysEqual(
            self.synthetic_barometer_channel.timestamps_microseconds_utc(),
            self.as_array([1, 2, 3, 4, 5]))

        self.assertArraysEqual(
            self.example_barometer_channel.timestamps_microseconds_utc(),
            self.as_array([1532656848120309, 1532656848318700, 1532656848517192, 1532656848717325, 1532656848916732,
                           1532656849116496,
                           1532656849313872, 1532656849515699, 1532656849713610, 1532656849913589, 1532656850112718,
                           1532656850312694,
                           1532656850509970, 1532656850709973, 1532656850909583, 1532656851108690, 1532656851308005,
                           1532656851506732,
                           1532656851706341, 1532656851905340, 1532656852104086, 1532656852304462, 1532656852509790,
                           1532656852702053,
                           1532656852901690, 1532656853100666, 1532656853300182, 1532656853499909, 1532656853698365,
                           1532656853897285,
                           1532656854096958, 1532656854296777, 1532656854496675, 1532656854694922, 1532656854895054,
                           1532656855093061,
                           1532656855291976, 1532656855492816, 1532656855691301, 1532656855890306, 1532656856090416,
                           1532656856290025,
                           1532656856490844, 1532656856688744, 1532656856888464, 1532656857086498, 1532656857287842,
                           1532656857485392,
                           1532656857688394, 1532656857884050, 1532656858084086, 1532656858283023, 1532656858483291,
                           1532656858682984,
                           1532656858880676, 1532656859079888, 1532656859278764, 1532656859478335, 1532656859677667,
                           1532656859877474,
                           1532656860076550, 1532656860275153, 1532656860475370, 1532656860674010, 1532656860873751,
                           1532656861072968,
                           1532656861272919, 1532656861472749, 1532656861672020, 1532656861869631, 1532656862069941,
                           1532656862269060,
                           1532656862468355, 1532656862667100, 1532656862866739, 1532656863065743, 1532656863265034,
                           1532656863463510,
                           1532656863663138, 1532656863863028, 1532656864061483, 1532656864261065, 1532656864459708,
                           1532656864658273,
                           1532656864858137, 1532656865058057, 1532656865257306, 1532656865456125, 1532656865657061,
                           1532656865855774,
                           1532656866055278, 1532656866253577, 1532656866453690, 1532656866654109, 1532656866852447,
                           1532656867052714,
                           1532656867251551, 1532656867453304, 1532656867650851, 1532656867853297, 1532656868049097,
                           1532656868253620,
                           1532656868447510, 1532656868646977, 1532656868847022, 1532656869046091, 1532656869244841,
                           1532656869444113,
                           1532656869644485, 1532656869841853, 1532656870042958, 1532656870241338, 1532656870440900,
                           1532656870639679,
                           1532656870838529, 1532656871038299, 1532656871237691, 1532656871436915, 1532656871636456,
                           1532656871835807,
                           1532656872034939, 1532656872234028, 1532656872433092, 1532656872632100, 1532656872830004,
                           1532656873030696,
                           1532656873229892, 1532656873428990, 1532656873628668, 1532656873828076, 1532656874026559,
                           1532656874227178,
                           1532656874425263, 1532656874622457, 1532656874823841, 1532656875022951, 1532656875222629,
                           1532656875421833,
                           1532656875620793, 1532656875819442, 1532656876019027, 1532656876219127, 1532656876417791,
                           1532656876617745,
                           1532656876816748, 1532656877015830, 1532656877216006, 1532656877415365, 1532656877615580,
                           1532656877814774,
                           1532656878016839, 1532656878213146, 1532656878414510, 1532656878610837, 1532656878817675,
                           1532656879010666,
                           1532656879209622, 1532656879408609, 1532656879607692, 1532656879807409, 1532656880006802,
                           1532656880205695,
                           1532656880405393, 1532656880604393, 1532656880803157, 1532656881003865, 1532656881203250,
                           1532656881402511,
                           1532656881601815, 1532656881799891, 1532656882000512, 1532656882199525, 1532656882399164,
                           1532656882597726,
                           1532656882796571, 1532656882996356, 1532656883196031, 1532656883395082, 1532656883595028,
                           1532656883793186,
                           1532656883992391, 1532656884191077, 1532656884390637, 1532656884590464, 1532656884789349,
                           1532656884991922,
                           1532656885191364, 1532656885389234, 1532656885587499, 1532656885784227, 1532656885986666,
                           1532656886183009,
                           1532656886383836, 1532656886583689, 1532656886782356, 1532656886982780, 1532656887182884,
                           1532656887381465,
                           1532656887579715, 1532656887782524, 1532656887978229, 1532656888178365, 1532656888377764,
                           1532656888578576,
                           1532656888776130, 1532656888976743, 1532656889174711, 1532656889377178, 1532656889573541,
                           1532656889772448,
                           1532656889971462, 1532656890170595, 1532656890369785, 1532656890570024, 1532656890769250,
                           1532656890968626,
                           1532656891167287, 1532656891369320, 1532656891566206, 1532656891765826, 1532656891964633,
                           1532656892165843,
                           1532656892363773, 1532656892562917, 1532656892762493, 1532656892960862, 1532656893160016,
                           1532656893359626,
                           1532656893558706, 1532656893757716, 1532656893957379, 1532656894156555, 1532656894356235,
                           1532656894555862,
                           1532656894754839, 1532656894955268, 1532656895155070, 1532656895354013, 1532656895553406,
                           1532656895752901,
                           1532656895951399, 1532656896151616, 1532656896349569, 1532656896549936, 1532656896747805,
                           1532656896948210,
                           1532656897147473, 1532656897349558, 1532656897546014, 1532656897745711, 1532656897944000,
                           1532656898145082,
                           1532656898343897, 1532656898543902, 1532656898746456, 1532656898942597, 1532656899143359]))

    def test_sample_interval_mean(self):
        self.assertEqual(self.synthetic_barometer_channel.sample_interval_mean(), 1.0)
        self.assertAlmostEqual(self.example_barometer_channel.sample_interval_mean(), 199308.7890625, 2)

    def test_sample_interval_std(self):
        self.assertEqual(self.synthetic_barometer_channel.sample_interval_std(), 2.0)
        self.assertAlmostEqual(self.example_barometer_channel.sample_interval_std(), 1546.7734115750022, 2)

    def test_sample_interval_median(self):
        self.assertEqual(self.synthetic_barometer_channel.sample_interval_median(), 3.0)
        self.assertEqual(self.example_barometer_channel.sample_interval_median(), 199267.0)

    def test_metadata_as_dict(self):
        synthetic_dict = self.synthetic_barometer_channel.metadata_as_dict()
        self.assertEqual(len(synthetic_dict), 1)
        self.assertTrue("foo" in synthetic_dict)
        self.assertEqual(synthetic_dict["foo"], "baz")
        self.assertEqual(len(self.example_barometer_channel.metadata_as_dict()), 0)


class TestUnevenlyXyzSampledSensor(ArraysTestCase):
    def setUp(self):
        self.base_packet: api900_pb2.RedvoxPacket = tests.mock_packets.synthetic_accelerometer_packet()
        self.wrapped_synthetic_packet = reader.wrap(self.base_packet)
        self.wrapped_example_packet = reader.wrap(reader.read_file("0000001314_1532656864354.rdvxz"))
        self.synthetic_accelerometer_channel = self.wrapped_synthetic_packet.accelerometer_channel()
        self.example_accelerometer_channel = self.wrapped_example_packet.accelerometer_channel()

    def test_x_type(self):
        self.assertEqual(self.synthetic_accelerometer_channel.x_type, api900_pb2.ACCELEROMETER_X)
        self.assertEqual(self.example_accelerometer_channel.x_type, api900_pb2.ACCELEROMETER_X)

    def test_y_type(self):
        self.assertEqual(self.synthetic_accelerometer_channel.y_type, api900_pb2.ACCELEROMETER_Y)
        self.assertEqual(self.example_accelerometer_channel.y_type, api900_pb2.ACCELEROMETER_Y)

    def test_z_type(self):
        self.assertEqual(self.synthetic_accelerometer_channel.z_type, api900_pb2.ACCELEROMETER_Z)
        self.assertEqual(self.example_accelerometer_channel.z_type, api900_pb2.ACCELEROMETER_Z)

    def test_payload_values(self):
        self.assertArraysEqual(self.synthetic_accelerometer_channel.payload_values(),
                               self.as_array([19.0, 155.0, 1.0,
                                              20.0, 156.0, 2.0,
                                              21.0, 157.0, 3.0,
                                              22.0, 158.0, 4.0,
                                              23.0, 159.0, 5.0]))

        self.assertSampledArray(self.example_accelerometer_channel.payload_values(),
                                1923,
                                [0, 1000, 1922],
                                [0.008989036083221436, -0.013596579432487488, 0.14465837180614471])

    def test_payload_values_x(self):
        self.assertArraysEqual(self.synthetic_accelerometer_channel.payload_values_x(),
                               self.as_array([19.0, 20.0, 21.0, 22.0, 23.0]))

        self.assertSampledArray(self.example_accelerometer_channel.payload_values_x(),
                                641,
                                [0, 320, 640],
                                [0.008989036083221436, -0.000293680903268978, 0.0012815780937671661])

    def test_payload_values_y(self):
        self.assertArraysEqual(self.synthetic_accelerometer_channel.payload_values_y(),
                               self.as_array([155.0, 156.0, 157.0, 158.0, 159.0]))
        self.assertSampledArray(self.example_accelerometer_channel.payload_values_y(),
                                641,
                                [0, 320, 640],
                                [0.017283279448747635, -0.012362873181700706, 0.013103981502354145])

    def test_payload_values_z(self):
        self.assertArraysEqual(self.synthetic_accelerometer_channel.payload_values_z(),
                               self.as_array([1.0, 2.0, 3.0, 4.0, 5.0]))
        self.assertSampledArray(self.example_accelerometer_channel.payload_values_z(),
                                641,
                                [0, 320, 640],
                                [0.1512121856212616, 0.14783009886741638, 0.14465837180614471])

    def test_payload_values_x_mean(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_x_mean(), 1)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_x_mean(), -0.0071045179466919265, 5)

    def test_payload_values_y_mean(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_y_mean(), 2)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_y_mean(), 0.00195356165569363, 5)

    def test_payload_values_z_mean(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_z_mean(), 3)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_z_mean(), 0.13963747286207265, 5)

    def test_payload_values_x_median(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_x_median(), 1)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_x_median(), -0.007555599324405193, 5)

    def test_payload_values_y_median(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_y_median(), 2)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_y_median(), 0.0014603914460167289, 5)

    def test_payload_values_z_median(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_z_median(), 3)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_z_median(), 0.14029136300086975, 5)

    def test_payload_values_x_std(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_x_std(), 1)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_x_std(), 0.02499872320189799, 5)

    def test_payload_values_y_std(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_y_std(), 2)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_y_std(), 0.02656895584776545, 5)

    def test_payload_values_z_std(self):
        self.assertEqual(self.synthetic_accelerometer_channel.payload_values_z_std(), 3)
        self.assertAlmostEqual(self.example_accelerometer_channel.payload_values_z_std(), 0.01730884582806553, 5)

class TestMicrophoneSensor(unittest.TestCase):
    pass


class TestBarometerSensor(unittest.TestCase):
    pass


class TestLocationSensor(unittest.TestCase):
    pass


class TestTimeSynchronizationSensor(unittest.TestCase):
    pass


class TestAccelerometerSensor(unittest.TestCase):
    pass


class TestMagnetometerSensor(unittest.TestCase):
    pass


class TestGyroscopeSensor(unittest.TestCase):
    pass


class TestLightSensor(unittest.TestCase):
    pass
