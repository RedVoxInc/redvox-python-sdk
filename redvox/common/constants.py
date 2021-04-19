"""
This is an auxiliary file where regularly used constants can be stored and exported.
"""

# noinspection Mypy
import numpy as np


GRAVITY_M_PER_S2: float = 9.80665  # acceleration of gravity in m/s^2
AVG_SEA_LEVEL_PRESSURE_KPA = (
    101.325  # average sea level pressure around the world in kPa
)
MOLAR_MASS_AIR_KG_PER_MOL = 0.02896  # molar mass of air in kg per mol
STANDARD_TEMPERATURE_K = 288.15  # standard surface temperature in K
UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2 = (
    8.3143  # universal gas constant in (kg * m^2) / (K * mol * s^2)
)
# constant used in barometric formula
#   source: https://www.math24.net/barometric-formula/
MG_DIV_BY_RT = (MOLAR_MASS_AIR_KG_PER_MOL * GRAVITY_M_PER_S2) / (
    STANDARD_TEMPERATURE_K * UNIVERSAL_GAS_CONSTANT_KG_M2_PER_K_MOL_S2
)

EARTH_RADIUS_M = 6367000.0  # earth's estimated radius in meters

KPA_TO_PA: float = 1000.0  # kilopascals in one pascal
EPSILON: float = np.finfo(np.float32).eps
PI: float = np.pi
DEG_TO_RAD = PI / 180.0  # converts degrees to radians
RAD_TO_DEG = 180.0 / PI  # converts radians to degrees

SECONDS_PER_HOUR: int = 3_600
SECONDS_PER_DAY: int = 86_400

NAN: float = float("nan")
