"""
This module contains functions for computing the cross correlation between data sets of equal or unequal length.
"""

from typing import Tuple

import numpy as np
from scipy import signal

import redvox.common.errors as errors


def xcorr_all(
    sig: np.ndarray, sig_ref: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generalized two-sensor cross correlation, including unequal lengths.

    :param sig: The original signal with the same sample rate in Hz as sig_ref.
    :param sig_ref: The reference signal with the same sample rate in Hz as sig..
    :return: A 4-tuple containing xcorr_indexes, xcorr, xcorr_offset_index, and xcorr_offset_samples. xcorr_indexes
             are relative to sig_ref. xcorr is the normalized cross-correlation. xcorr_offset_index contains the index
             of max xcorr. xcorr_offset_samples is the number of offset samples for xcorr.
    """
    # Generalized two-sensor cross correlation, including unequal lengths
    # Same as main, but more outputs
    sig_len: int = len(sig)
    ref_len: int = len(sig_ref)
    # Faster as floats
    sig = 1.0 * sig
    sig_ref = 1.0 * sig_ref
    if sig_len > ref_len:
        # Cross Correlation 'full' sums over the dimension of sigX
        xcorr_indexes: np.ndarray = np.arange(1 - sig_len, ref_len)
        xcorr: np.ndarray = signal.correlate(sig_ref, sig, mode="full")
        # Normalize
        xcorr /= np.sqrt(sig_len * ref_len) * sig.std() * sig_ref.std()
        xcorr_offset_index: np.ndarray = xcorr.argmax()
        xcorr_offset_samples: np.ndarray = xcorr_indexes[xcorr_offset_index]
    elif sig_len < ref_len:
        # Cross Correlation 'full' sums over the dimension of sigY
        xcorr_indexes = np.arange(1 - ref_len, sig_len)
        xcorr = signal.correlate(sig, sig_ref, mode="full")
        # Normalize
        xcorr /= np.sqrt(sig_len * ref_len) * sig.std() * sig_ref.std()
        xcorr_offset_index = xcorr.argmax()
        # Flip sign
        xcorr_offset_samples = -xcorr_indexes[xcorr_offset_index]
    elif sig_len == ref_len:
        # Cross correlation is centered in the middle of the record and has length sig_len
        # Fastest, o(sig_len) and can use FFT solution
        if sig_len % 2 == 0:
            xcorr_indexes = np.arange(-int(sig_len / 2), int(sig_len / 2))
        else:
            xcorr_indexes = np.arange(-int(sig_len / 2), int(sig_len / 2) + 1)

        xcorr = signal.correlate(sig_ref, sig, mode="same")
        # Normalize
        xcorr /= np.sqrt(sig_len * ref_len) * sig.std() * sig_ref.std()
        xcorr_offset_index = xcorr.argmax()
        xcorr_offset_samples = xcorr_indexes[xcorr_offset_index]
    else:
        raise errors.RedVoxError("One of the waveforms is broken")

    return xcorr_indexes, xcorr, xcorr_offset_index, xcorr_offset_samples


def xcorr_main(
    sig: np.ndarray, sig_ref: np.ndarray, sample_rate_hz: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generalized two-sensor cross correlation, including unequal lengths. Provides summarized results.

    :param sig: The original signal with the same sample rate in Hz as sig_ref.
    :param sig_ref: The reference signal with the same sample rate in Hz as sig.
    :param sample_rate_hz: The sample rate in Hz.
    :return: A 3-tuple containing xcorr_normalized_max, xcorr_offset_samples, and xcorr_offset_seconds.
             Where xcorr_normalized_max is the maxx xcorr, xcorr_offset_samples is the number of offset samples for the
             max xcorr, and xcorr_offset_seconds is samples converted to offset seconds for the max xcorr,
             requires sample rate in Hz.
    """

    xcorr_result: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] = xcorr_all(
        sig, sig_ref
    )
    xcorr: np.ndarray = xcorr_result[1]
    xcorr_offset_samples: np.ndarray = xcorr_result[3]

    # noinspection PyArgumentList
    xcorr_normalized_max: np.ndarray = xcorr.max()
    xcorr_offset_seconds: np.ndarray = xcorr_offset_samples / sample_rate_hz

    return xcorr_normalized_max, xcorr_offset_samples, xcorr_offset_seconds
