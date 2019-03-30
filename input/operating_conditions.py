import numpy as np


""" This file contains the geometry data"""

"""Electrochemistry"""
# target current density [A/m^2]
#target_current_density = np.linspace(1.e-3, 10000., 20)
target_current_density = np.array([4000., 8000.])
# open circuit voltage [V]
open_circuit_voltage = 0.95
# cathode stoichiometry
stoichiometry_cathode = 2.5
# anode stoichiometry
stoichiometry_anode = 2.
# pem-type (True = HT-PEM, False = NT-PEM)
is_ht_pem = True

""""Thermal Settings"""
# air inlet temperature [K]
temp_air_in = 433.15
# anode gas inlet temperature [K]
temp_anode_gas_in = 433.15
# coolant inlet temperature [K]
temp_coolant_in = 433.15
# environment temperature [K]
temp_environment = 298.15
# heat power of the endplates [W]
endplates_heat_power = 0.e0
# initial temperature [K]
temp_initial = 433.15

"""Fluid Mechanic Settings"""
# pressure at the outlet of the cathode manifold [Pa]
p_manifold_cathode_out = 1.e5
# pressure at the outlet of the anode manifold [Pa]
p_manifold_anode_out = 1.e5
# mass flow of the coolant per channel [kg/s]
mass_flow_coolant = 1.e-4

# flow directions (1 is along the x-axis, -1 the opposite direction)
anode_flow_direction = -1
cathode_flow_direction = 1

"""Cell Settings"""


"""Stack Settings"""
# number of the pemfc
cell_number = 3
# coolant channel configuration (no cooling channel at the endplates = False)
cooling_bc = True
