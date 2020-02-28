"""
This module contains functions for computing the cross correlation between data sets.
"""

from typing import Tuple

import numpy as np
from scipy import signal

import redvox.common.errors as errors


def xcorr_all(sig: np.ndarray, sig_ref: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Generalized two-sensor cross correlation, including unequal lengths.
    :param sig: The original signal.
    :param sig_ref: The reference signal.
    :return: A 4-tuple containing xcorr_indexes, xcorr, xcorr_offset_index, and xcorr_offset_samples.
    """
    # Generalized two-sensor cross correlation, including unequal lengths
    # Same as main, but more outputs
    NX = len(sig)
    NREF = len(sig_ref)
    # Faster as floats
    sig = 1.0 * sig
    sig_ref = 1.0 * sig_ref
    if NX > NREF:
        # Cross Correlation 'full' sums over the dimension of sigX
        xcorr_indexes = np.arange(1 - NX, NREF)
        xcorr = signal.correlate(sig_ref, sig, mode='full')
        # Normalize
        xcorr /= np.sqrt(NX * NREF) * sig.std() * sig_ref.std()
        xcorr_offset_index = xcorr.argmax()
        xcorr_offset_samples = xcorr_indexes[xcorr_offset_index]
    elif NX < NREF:
        # Cross Correlation 'full' sums over the dimension of sigY
        xcorr_indexes = np.arange(1 - NREF, NX)
        xcorr = signal.correlate(sig, sig_ref, mode='full')
        # Normalize
        xcorr /= np.sqrt(NX * NREF) * sig.std() * sig_ref.std()
        xcorr_offset_index = xcorr.argmax()
        # Flip sign
        xcorr_offset_samples = -xcorr_indexes[xcorr_offset_index]
    elif NX == NREF:
        # Cross correlation is centered in the middle of the record and has length NX
        # Fastest, o(NX) and can use FFT solution
        if NX % 2 == 0:
            xcorr_indexes = np.arange(-int(NX / 2), int(NX / 2))
        else:
            xcorr_indexes = np.arange(-int(NX / 2), int(NX / 2) + 1)

        xcorr = signal.correlate(sig_ref, sig, mode='same')
        # Normalize
        xcorr /= np.sqrt(NX * NREF) * sig.std() * sig_ref.std()
        xcorr_offset_index = xcorr.argmax()
        xcorr_offset_samples = xcorr_indexes[xcorr_offset_index]
    else:
        raise errors.RedVoxError('One of the waveforms is broken')

    return xcorr_indexes, xcorr, xcorr_offset_index, xcorr_offset_samples


def xcorr_main(sig: np.ndarray,
               sig_ref: np.ndarray,
               sample_rate_hz: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generalized two-sensor cross correlation, including unequal lengths.
    :param sig: The original signal.
    :param sig_ref: The reference signal.
    :param sample_rate_hz: The sample rate in Hz.
    :return: A 3-tuple containing xcorr_normalized_max, xcorr_offset_samples, and xcorr_offset_seconds.
    """

    xcorr_result: Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] = xcorr_all(sig, sig_ref)
    xcorr: np.ndarray = xcorr_result[1]
    xcorr_offset_samples: np.ndarray = xcorr_result[3]

    # noinspection PyArgumentList
    xcorr_normalized_max = xcorr.max()
    xcorr_offset_seconds = xcorr_offset_samples / sample_rate_hz

    return xcorr_normalized_max, xcorr_offset_samples, xcorr_offset_seconds

