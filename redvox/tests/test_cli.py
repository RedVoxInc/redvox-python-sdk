import glob
import os
import shutil
import subprocess
import unittest

import redvox.api900.reader as reader
from redvox.tests.utils import test_data, TEST_DATA_DIR


class TestCli(unittest.TestCase):

    def setUp(self):
        # Make some copies of the test data so that they can be used here
        shutil.copyfile(test_data("example.rdvxz"), test_data("test_a.rdvxz"))
        shutil.copyfile(test_data("example.rdvxz"), test_data("test_b.rdvxz"))
        shutil.copyfile(test_data("example.json"), test_data("test_c.json"))
        shutil.copyfile(test_data("example.json"), test_data("test_d.json"))

    def tearDown(self):
        # Delete the copies from setUp
        test_files = glob.glob(TEST_DATA_DIR + "/test_*")
        for test_file in test_files:
            os.remove(test_file)

    def test_to_json_single(self):
        os.system("python3 -m redvox.api900.cli to_json %s" % test_data("test_a.rdvxz"))
        self.assertTrue(os.path.isfile(test_data("test_a.json")))
        self.assertEqual(reader.read_rdvxz_file(test_data("test_a.rdvxz")),
                         reader.read_json_file(test_data("test_a.json")))

    def test_to_json_multi(self):
        os.system("python3 -m redvox.api900.cli to_json %s/*.rdvxz" % TEST_DATA_DIR)
        self.assertTrue(os.path.isfile(test_data("test_a.json")))
        self.assertTrue(os.path.isfile(test_data("test_b.json")))
        self.assertEqual(reader.read_rdvxz_file(test_data("test_a.rdvxz")),
                         reader.read_json_file(test_data("test_a.json")))
        self.assertEqual(reader.read_rdvxz_file(test_data("test_b.rdvxz")),
                         reader.read_json_file(test_data("test_b.json")))

    def test_to_rdvxz_single(self):
        os.system("python3 -m redvox.api900.cli to_rdvxz %s" % test_data("test_c.json"))
        self.assertTrue(os.path.isfile(test_data("test_c.rdvxz")))
        self.assertEqual(reader.read_rdvxz_file(test_data("test_c.rdvxz")),
                         reader.read_json_file(test_data("test_c.json")))

    def test_to_rdvxz_multi(self):
        os.system("python3 -m redvox.api900.cli to_rdvxz %s/*.json" % TEST_DATA_DIR)
        self.assertTrue(os.path.isfile(test_data("test_c.rdvxz")))
        self.assertTrue(os.path.isfile(test_data("test_d.rdvxz")))
        self.assertEqual(reader.read_rdvxz_file(test_data("test_c.rdvxz")),
                         reader.read_json_file(test_data("test_c.json")))
        self.assertEqual(reader.read_rdvxz_file(test_data("test_d.rdvxz")),
                         reader.read_json_file(test_data("test_d.json")))

    def test_print_single(self):
        output: str = subprocess.check_output("python3 -m redvox.api900.cli print %s" % test_data("test_a.rdvxz"),
                                              shell=True).decode()
        self.assertTrue("api: 900" in output)

    def test_print_multi(self):
        output: str = subprocess.check_output("python3 -m redvox.api900.cli print %s/*.rdvxz" % TEST_DATA_DIR,
                                              shell=True).decode()
        self.assertEqual(len(list(filter(lambda line: line.startswith("api: 900"),
                                    output.split("\n")))),
                         3)

    def test_no_args(self):
        process = subprocess.Popen("python3 -m redvox.api900.cli", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("usage" in output)

    def test_cmd_no_args(self):
        process = subprocess.Popen("python3 -m redvox.api900.cli to_json", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("usage" in output)

        process = subprocess.Popen("python3 -m redvox.api900.cli to_rdvxz", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("usage" in output)

        process = subprocess.Popen("python3 -m redvox.api900.cli print", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("usage" in output)

    def test_bad_cmd(self):
        process = subprocess.Popen("python3 -m redvox.api900.cli bad", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("usage" in output)

    def test_bad_path(self):
        process = subprocess.Popen("python3 -m redvox.api900.cli to_json bad", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("Error: File with path" in output)

        process = subprocess.Popen("python3 -m redvox.api900.cli to_rdvxz bad", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("Error: File with path" in output)

        process = subprocess.Popen("python3 -m redvox.api900.cli print bad", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("Error: File with path" in output)

        process = subprocess.Popen("python3 -m redvox.api900.cli to_rdvxz *.whatever", stderr=subprocess.STDOUT, stdout=subprocess.PIPE, shell=True)
        output = process.communicate()[0].decode()
        self.assertTrue("Error: File with path" in output)