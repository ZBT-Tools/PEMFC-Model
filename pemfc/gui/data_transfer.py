# local module imports
from ..settings import simulation as sim, operating_conditions as op_con, \
    output as out, geometry as geom, physical_properties as phy_prop
from ..src import species
from ..src import global_functions as gf

from . import entry_value

nodes = sim.elements + 1


def gen_dict_extract(key, var):
    if hasattr(var, 'items'):
        for k, v in var.items():
            if k == key:
                yield var
            if isinstance(v, dict):
                for result in gen_dict_extract(key, v):
                    yield result
            elif isinstance(v, list):
                for d in v:
                    for result in gen_dict_extract(key, d):
                        yield result


def set_dict_entry(value, name_list, target_dict):
    if isinstance(target_dict, dict):
        sub_dict = target_dict
        for i in range(len(name_list) - 1):
            sub_dict = sub_dict[name_list[i]]
        if isinstance(value, entry_value.EntryValue):
            value = value.value
        sub_dict[name_list[-1]] = value
        return target_dict


def transfer(source_dict, target_dict):
    # loop through tab frames of gui notebook
    # for ki, vi in gui_values.items():
    #     for kj, vj in vi.items():
    #         print(kj, vj, '\n')

    # get only widgets with sim_names
    extracted_gui_entries = list(gen_dict_extract('sim_name', source_dict))
    if extracted_gui_entries:
        for gui_entry in extracted_gui_entries:
            sim_names = gui_entry['sim_name']
            sim_names = gf.ensure_list(sim_names)
            sub_dict = target_dict

            if isinstance(sim_names[0], list):
                gui_values = gf.ensure_list(gui_entry['value'])
                if len(sim_names) != len(gui_values):
                    gui_values = [gui_values[0] for i in range(len(sim_names))]
                for i, name in enumerate(sim_names):
                    sub_dict = set_dict_entry(gui_values[i], name, sub_dict)
            else:
                sub_dict = \
                    set_dict_entry(gui_entry['value'], sim_names, sub_dict)
        print(sub_dict)
    return target_dict


sim_dict = {
    'stack': {
        'cell_number': geom.cell_number,
        'heat_power': op_con.endplates_heat_power,
        'cool_flow': geom.coolant_circuit,
        'calc_temperature': sim.calc_temperature,
        'calc_current_density': sim.calc_electricity,
        # 'calc_flow_distribution': sim.calc_flow_distribution,
        'init_current_density': op_con.current_density
        },
    'simulation': {
        'maximum_iteration': sim.maximum_iteration_number,
        'minimum_iteration': sim.minimum_iteration_number,
        'iteration_criteria': sim.convergence_criteria,
        'current_control': op_con.current_control,
        'nodes': nodes,
        'current_density': getattr(op_con, 'current_density', None),
        'average_cell_voltage': getattr(op_con, 'average_cell_voltage', None)
        },
    'cell': {
        'width': geom.cell_width,
        'length': geom.cell_length,
        'thermal conductivity bpp':
            (phy_prop.thermal_conductivity_bipolar_plate_z,
             phy_prop.thermal_conductivity_bipolar_plate_x),
        'thermal conductivity gde':
            (phy_prop.thermal_conductivity_gas_diffusion_electrode_z,
             phy_prop.thermal_conductivity_gas_diffusion_electrode_x),
        'electrical conductivity bpp':
            phy_prop.electrical_conductivity_bipolar_plate,
        'electrical conductivity gde':
            phy_prop.electrical_conductivity_gde,
        'temp_cool_in': op_con.temp_coolant_in,
        'mem_base_r': phy_prop.membrane_basic_resistance,
        'mem_acl_r': phy_prop.membrane_temperature_coefficient,
        'temp_init': op_con.temp_initial,
        'underrelaxation_factor': sim.underrelaxation_factor,
        'open_circuit_voltage': op_con.open_circuit_voltage,
        'thermoneutral_voltage': phy_prop.v_thermo_neutral
        },
    'membrane': {
        'type': phy_prop.membrane_type,
        'thickness': geom.membrane_thickness,
        'acid group concentration':
            phy_prop.molar_membrane_acid_group_concentration,
        'vapour transport coefficient':
            phy_prop.vapour_mass_transport_coefficient,
        'ionic conductivity': phy_prop.membrane_basic_conductivity,
        'basic resistance': phy_prop.membrane_basic_resistance,
        'temperature coefficient':
            phy_prop.membrane_temperature_coefficient,
        'thermal conductivity':
            (phy_prop.thermal_conductivity_membrane_z,
             phy_prop.thermal_conductivity_membrane_x),
        'calc_loss': sim.calc_membrane_loss
        },
    'cathode': {
        'name': 'Cathode',
        'flow_direction': geom.cathode_flow_direction,
        'channel_number': geom.cathode_channel_number,
        'stoichiometry': op_con.stoichiometry_cathode,
        'is_cathode': True,
        'species_names': op_con.cathode_species,
        'inlet_composition': op_con.cathode_inlet_composition,
        'charge_number': op_con.cathode_electron_number,
        'reaction_stoichiometry': op_con.cathode_reaction_stoich,
        'thickness_cl': geom.cathode_catalyst_layer_thickness,
        'thickness_gdl': geom.cathode_gdl_thickness,
        'thickness_bpp': geom.cathode_bipolar_plate_thickness,
        'porosity_cl': geom.cathode_catalyst_layer_porosity,
        'porosity_gdl': geom.cathode_gdl_porosity,
        'tafel_slope': phy_prop.tafel_slope_cathode,
        'prot_con_cl': phy_prop.catalyst_layer_proton_conductivity_cathode,
        'vol_ex_cd': phy_prop.exchange_current_density_cathode,
        'diff_coeff_cl': phy_prop.oxygen_catalyst_layer_diffusion_coefficient,
        'diff_coeff_gdl':
            phy_prop.oxygen_gas_diffusion_layer_diffusion_coefficient,
        'calc_act_loss': sim.calc_activation_loss,
        'calc_cl_diff_loss': sim.calc_cl_loss,
        'calc_gdl_diff_loss': sim.calc_gdl_loss,
        'c_eps': sim.c_eps,
        'delta_i': sim.delta_i,
        'channel': {
            'name': 'Cathode Channel',
            'fluid': {
                'name': 'Cathode Gas',
                'fluid_components': op_con.cathode_species,
                'inlet_composition': op_con.cathode_inlet_composition,
                'temp_init': op_con.temp_cathode_in,
                'press_init': op_con.p_manifold_cathode_out,
                'nodes': nodes
                },
            'length': geom.cathode_channel_length,
            'p_out': op_con.p_manifold_cathode_out,
            'temp_in': op_con.temp_cathode_in,
            'flow_direction': geom.cathode_flow_direction,
            'width': geom.cathode_channel_width,
            'height': geom.cathode_channel_height,
            'bend_number': geom.cathode_channel_bends,
            'bend_friction_factor': geom.bend_pressure_loss_coefficient
            },
        'flow circuit': {
            'name': 'Cathode Flow Circuit',
            'type': geom.cathode_manifold_model,
            'shape': geom.cathode_manifold_configuration,
            'calc_distribution': geom.calc_cathode_distribution,
            'tolerance': sim.convergence_criteria_flow,
            'min_iter': sim.minimum_iteration_number_flow,
            'max_iter': sim.maximum_iteration_number_flow,
            'underrelaxation_factor': sim.underrelaxation_factor,
            'inlet manifold': {
                'name': 'Cathode Inlet Manifold',
                'length': None,
                'p_out': op_con.p_manifold_cathode_out,
                'temp_in': op_con.temp_cathode_in,
                'flow_direction': 1,
                'cross_sectional_shape': geom.cathode_manifold_cross_shape,
                'diameter': geom.cathode_in_manifold_diameter,
                'width': geom.cathode_in_manifold_width,
                'height': geom.cathode_in_manifold_height,
                'bend_number': 0,
                'bend_friction_factor': 0.0,
                'constant_friction_factor':
                    geom.cathode_in_manifold_pressure_loss_coefficient
                },
            'outlet manifold': {
                'name': 'Cathode Outlet Manifold',
                'length': None,
                'p_out': op_con.p_manifold_cathode_out,
                'temp_in': op_con.temp_cathode_in,
                'flow_direction': 1,
                'cross_sectional_shape': geom.cathode_manifold_cross_shape,
                'diameter': geom.cathode_out_manifold_diameter,
                'width': geom.cathode_out_manifold_width,
                'height': geom.cathode_out_manifold_height,
                'bend_number': 0,
                'bend_friction_factor': 0.0,
                'constant_friction_factor':
                    geom.cathode_out_manifold_pressure_loss_coefficient
                }
            }
        },
    'anode': {
        'name': 'Anode',
        'flow_direction': geom.anode_flow_direction,
        'channel_number': geom.anode_channel_number,
        'stoichiometry': op_con.stoichiometry_anode,
        'is_cathode': False,
        'species_names': op_con.anode_species,
        'inlet_composition': op_con.anode_inlet_composition,
        'charge_number': op_con.anode_electron_number,
        'reaction_stoichiometry': op_con.anode_reaction_stoich,
        'thickness_cl': geom.anode_catalyst_layer_thickness,
        'thickness_gdl': geom.anode_gdl_thickness,
        'thickness_bpp': geom.anode_bipolar_plate_thickness,
        'porosity cl': geom.anode_catalyst_layer_porosity,
        'porosity gdl': geom.anode_gdl_porosity,
        'tafel_slope': phy_prop.tafel_slope_anode,
        'prot_con_cl': phy_prop.catalyst_layer_proton_conductivity_anode,
        'vol_ex_cd': phy_prop.exchange_current_density_anode,
        'diff_coeff_cl': phy_prop.hydrogen_catalyst_layer_diffusion_coefficient,
        'diff_coeff_gdl':
            phy_prop.hydrogen_diffusion_layer_diffusion_coefficient,
        'calc_act_loss': sim.calc_activation_loss,
        'calc_cl_diff_loss': sim.calc_cl_loss,
        'calc_gdl_diff_loss': sim.calc_gdl_loss,
        'c_eps': sim.c_eps,
        'delta_i': sim.delta_i,
        'channel': {
            'name': 'Anode Channel',
            'fluid': {
                'name': 'Anode Gas',
                'fluid_components': op_con.anode_species,
                'inlet_composition': op_con.anode_inlet_composition,
                'temp_init': op_con.temp_anode_in,
                'press_init': op_con.p_manifold_anode_out,
                'nodes': nodes
                },
            'length': geom.anode_channel_length,
            'p_out': op_con.p_manifold_anode_out,
            'temp_in': op_con.temp_anode_in,
            'flow_direction': geom.anode_flow_direction,
            'width': geom.anode_channel_width,
            'height': geom.anode_channel_height,
            'bend_number': geom.anode_channel_bends,
            'bend_friction_factor': geom.bend_pressure_loss_coefficient
            },
        'flow circuit': {
            'name': 'Anode Flow Circuit',
            'type': geom.anode_manifold_model,
            'shape': geom.anode_manifold_configuration,
            'calc_distribution': geom.calc_anode_distribution,
            'tolerance': sim.convergence_criteria_flow,
            'min_iter': sim.minimum_iteration_number_flow,
            'max_iter': sim.maximum_iteration_number_flow,
            'underrelaxation_factor': sim.underrelaxation_factor,
            'inlet manifold': {
                'name': 'Anode Inlet Manifold',
                'length': None,
                'p_out': op_con.p_manifold_anode_out,
                'temp_in': op_con.temp_anode_in,
                'flow_direction': 1,
                'cross_sectional_shape': geom.anode_manifold_cross_shape,
                'diameter': geom.anode_in_manifold_diameter,
                'width': geom.anode_in_manifold_width,
                'height': geom.anode_in_manifold_height,
                'bend_number': 0,
                'bend_friction_factor': 0.0,
                'constant_friction_factor':
                    geom.anode_in_manifold_pressure_loss_coefficient
                },
            'outlet manifold': {
                'name': 'Anode Outlet Manifold',
                'length': None,
                'p_out': op_con.p_manifold_anode_out,
                'temp_in': op_con.temp_anode_in,
                'flow_direction': 1,
                'cross_sectional_shape': geom.anode_manifold_cross_shape,
                'diameter': geom.anode_out_manifold_diameter,
                'width': geom.anode_out_manifold_width,
                'height': geom.anode_out_manifold_height,
                'bend_number': 0,
                'bend_friction_factor': 0.0,
                'constant_friction_factor':
                    geom.anode_out_manifold_pressure_loss_coefficient
                }
            }
        },
    'coolant channel': {
        'name': 'Coolant Channel',
        'fluid': {
            'name': 'Coolant Fluid',
            'fluid_components': None,
            'inlet_composition': None,
            'liquid_props':
                species.ConstantProperties(
                    phy_prop.coolant_name,
                    specific_heat=phy_prop.heat_capacity_coolant,
                    density=phy_prop.density_coolant,
                    viscosity=phy_prop.dynamic_viscosity_coolant,
                    thermal_conductivity=phy_prop.thermal_conductivity_coolant),
            'temp_init': op_con.temp_coolant_in,
            'press_init': op_con.p_manifold_anode_out,
            'nodes': nodes
            },
        'length': geom.coolant_channel_length,
        'p_out': op_con.p_manifold_cathode_out,
        'temp_in': op_con.temp_coolant_in,
        'flow_direction': geom.cathode_flow_direction,
        'width': geom.coolant_channel_width,
        'height': geom.coolant_channel_height,
        'bend_number': geom.coolant_channel_bends,
        'bend_friction_factor': geom.coolant_bend_pressure_loss_coefficient
        },
    'coolant flow circuit': {
        'name': 'Coolant Flow Circuit',
        'type': geom.coolant_manifold_model,
        'shape': geom.coolant_manifold_configuration,
        'calc_distribution': geom.calc_coolant_distribution,
        'tolerance': sim.convergence_criteria_flow,
        'min_iter': sim.minimum_iteration_number_flow,
        'max_iter': sim.maximum_iteration_number_flow,
        'inlet manifold': {
            'name': 'Coolant Inlet Manifold',
            'p_out': op_con.p_manifold_cathode_out,
            'temp_in': op_con.temp_coolant_in,
            'flow_direction': 1,
            'cross_sectional_shape': geom.coolant_manifold_cross_shape,
            'diameter': geom.coolant_in_manifold_diameter,
            'width': geom.coolant_in_manifold_width,
            'height': geom.coolant_in_manifold_height,
            'bend_number': 0,
            'bend_friction_factor': 0.0,
            'constant_friction_factor':
                geom.coolant_in_manifold_pressure_loss_coefficient
            },
        'outlet manifold': {
            'name': 'Coolant Inlet Manifold',
            'p_out': op_con.p_manifold_cathode_out,
            'temp_in': op_con.temp_coolant_in,
            'flow_direction': 1,
            'cross_sectional_shape': geom.coolant_manifold_cross_shape,
            'diameter': geom.coolant_out_manifold_diameter,
            'width': geom.coolant_out_manifold_width,
            'height': geom.coolant_out_manifold_height,
            'bend_number': 0,
            'bend_friction_factor': 0.0,
            'constant_friction_factor':
                geom.coolant_out_manifold_pressure_loss_coefficient
            }
        },
    'temperature system': {
        'temp_amb': op_con.temp_environment,
        'alpha_amb': op_con.convection_coefficient_environment,
        'heat_pow': op_con.endplates_heat_power,
        'cool_ch_bc': geom.cooling_bc,
        'cool_ch_numb': geom.coolant_channel_number,
        'cool_temp_diff': getattr(op_con, 'coolant_temperature_difference',
                                  None),
        'cool_mass_flow': getattr(op_con, 'coolant_mass_flow', None)
        },
    'output': {
        'save_csv': out.save_csv_data,
        'save_plot': out.save_plot_data,
        'show_loss': getattr(out, 'show_voltage_loss', False),
        'directory': out.directory
        }
    }
