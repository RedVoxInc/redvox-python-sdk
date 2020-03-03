"""
 cross correlation test module
"""

import unittest
import redvox.common.cross_stats as cs
import numpy as np

SIGNAL_LENGTH = 100   # number of elements in signal
SAMPLE_RATE = 80.0    # sample rate in hz


class CrossCorrelationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sig = np.ndarray((SIGNAL_LENGTH,), float)
        self.sig_ref = np.ndarray((SIGNAL_LENGTH,), float)
        self.double_sig_ref = np.ndarray((SIGNAL_LENGTH * 2,), float)
        self.sample_rate = SAMPLE_RATE
        sign = 1.0
        for index in range(SIGNAL_LENGTH):
            self.sig[index] = (index % 25) * sign
            self.sig_ref[index] = ((index + 10) % 25) * sign
            self.double_sig_ref[index] = ((index - 7) % 25) * sign
            self.double_sig_ref[index + SIGNAL_LENGTH] = ((index - 10) % 25) * sign
            sign *= -1.0
        self.half_sig_ref = self.sig_ref[13:63]

    def test_xcorr_all(self):
        # sig length == ref length
        xcorr_indexes, xcorr, xcorr_offset_index, xcorr_offset_samples = cs.xcorr_all(self.sig, self.sig_ref)
        self.assertEqual(len(xcorr), 100)
        self.assertEqual(len(xcorr_indexes), 100)
        self.assertEqual(xcorr_offset_index, 40)
        self.assertEqual(xcorr_offset_samples, -10)
        # sig length < ref length
        xcorr_indexes, xcorr, xcorr_offset_index, xcorr_offset_samples = cs.xcorr_all(self.sig, self.double_sig_ref)
        self.assertEqual(len(xcorr), 299)
        self.assertEqual(len(xcorr_indexes), 299)
        self.assertEqual(xcorr_offset_index, 139)
        self.assertEqual(xcorr_offset_samples, 60)
        # sig length > ref length
        xcorr_indexes, xcorr, xcorr_offset_index, xcorr_offset_samples = cs.xcorr_all(self.sig, self.half_sig_ref)
        self.assertEqual(len(xcorr), 149)
        self.assertEqual(len(xcorr_indexes), 149)
        self.assertEqual(xcorr_offset_index, 76)
        self.assertEqual(xcorr_offset_samples, -23)

    def test_xcorr_main(self):
        xcorr_normalized_max, xcorr_offset_samples, xcorr_offset_seconds = \
            cs.xcorr_main(self.sig, self.sig_ref, self.sample_rate)
        self.assertAlmostEqual(xcorr_normalized_max, 0.9855, 4)
        self.assertEqual(xcorr_offset_samples, -10)
        self.assertEqual(xcorr_offset_seconds, -0.125)
