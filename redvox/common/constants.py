"""
This is an auxiliary file where regularly used constants can be stored and exported.
"""

# noinspection Mypy
import numpy as np


KPA_TO_PA: float = 1000.  # kilopascals in one pascal
GRAVITY: float = 9.80665  # acceleration of gravity in m/s^2
EPSILON: float = np.finfo(np.float32).eps
PI: float = np.pi
