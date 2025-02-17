"""Rescaling functions."""
from config import HV_SCALING_COEFFICIENT_A as A, \
    HV_SCALING_COEFFICIENT_B as B


def rescale_voltage(voltage: float):
    """Calculate FuG 3500 input voltage."""
    return min(10.0, max(0.0, (voltage - B) / A))
