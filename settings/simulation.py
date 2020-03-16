""" This file contains the simulation settings"""

"""Simulation Settings"""
# discretization of the flow channel along the x-axis
elements = 20
# convergence criteria of the simulation
convergence_criteria = 1.e-6
# maximum number of iterations
maximum_iteration_number = 100
# minimum number of iterations
minimum_iteration_number = 3
# calculate the PEMFC stack temperatures
calc_temperature = True
# calculate the current density distribution
calc_current_density = True
# calculate the flow distribution
calc_flow_distribution = True
# calculate the activation voltage losses
calc_activation_loss = True
# calculate the membrane voltage losses
calc_membrane_loss = True
# calculate gdl diffusion voltage losses
calc_gdl_loss = True
# calculate catalyst layer diffusion voltage losses
calc_cl_loss = True

