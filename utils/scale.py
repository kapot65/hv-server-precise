"""Rescaling functions."""
from config import HV_SCALING_COEFFICIENT_A, HV_SCALING_COEFFICIENT_B


def rescale_voltage(voltage: float):
    """Calculate FuG 3500 input voltage."""
    return min(10.0, max(0.0, (voltage - HV_SCALING_COEFFICIENT_B) / HV_SCALING_COEFFICIENT_A)) 
