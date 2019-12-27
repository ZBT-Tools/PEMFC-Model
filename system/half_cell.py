import warnings
import system.global_functions as g_func
import data.water_properties as w_prop
import data.gas_properties as g_prop
import numpy as np
import data.global_parameters as g_par
import system.channel as ch
import system.layers as layers
import sys
import system.interpolation as ip

warnings.filterwarnings("ignore")


class HalfCell:

    # Class variables constant across all instances of the class
    # (under construction)
    n_nodes = None
    n_ele = None
    fwd_mtx = None
    bwd_mtx = None

    def __init__(self, halfcell_dict, cell_dict, channel_dict):
        self.name = halfcell_dict['name']
        n_nodes = g_par.dict_case['nodes']
        n_ele = n_nodes - 1
        self.n_ele = n_ele
        # Discretization in elements and nodes along the x-axis (flow axis)

        """half cell geometry parameter"""
        self.width = cell_dict["width"]
        self.length = cell_dict["length"]

        # Initialize channel object
        self.channel = ch.Channel(channel_dict)

        # number of channels of each half cell
        self.n_chl = halfcell_dict['channel_number']
        area_factor = self.length * self.width \
            / (self.channel.base_area * self.n_chl)
        if area_factor < 1.0:
            raise ValueError('width and length of cell result in a cell '
                             'surface area  smaller than the area covered by '
                             'channels')

        self.rib_width = self.channel.width * (area_factor - 1.0)
        self.width_straight_channels = self.channel.width * self.n_chl \
            + self.rib_width * (self.n_chl + 1)
        self.length_straight_channels = (self.length * self.width) \
            / self.width_straight_channels
        self.active_area = area_factor * self.channel.base_area
        # self.active_area = area_factor * self.channel.base_area
        # factor active area with ribs / active channel area
        self.active_area_dx = area_factor * self.channel.base_area_dx
        # self.active_area_dx = area_factor * self.channel.base_area_dx

        self.flow_direction = halfcell_dict['flow_direction']
        if self.flow_direction not in (-1, 1):
            sys.exit('Member variable flow_direction of class HalfCell '
                     'must be either 1 or -1')
        if self.flow_direction == 1:
            self.ele_in = 0
        else:
            self.ele_in = -1
        self.id_fuel = 0
        self.id_h2o = 2
        self.id_inert = 1
        self.species_names = halfcell_dict['species_names']
        self.species = []
        for i, name in enumerate(self.species_names):
            for j in range(len(g_prop.species)):
                if name == g_prop.species[j].name:
                    self.species.append(g_prop.species[j])
                    break
        self.n_species = len(self.species_names)
        self.n_charge = halfcell_dict['charge_number']
        self.n_stoi = np.asarray(halfcell_dict['reaction_stoichiometry'])
        self.mol_mass = np.asarray(halfcell_dict['molar_mass'])
        # check if the object is an anode or a cathode
        # catalyst layer specific handover
        self.inlet_composition = halfcell_dict['inlet_composition']
        self.inert_reac_ratio = \
            self.inlet_composition[self.id_inert] \
            / self.inlet_composition[self.id_fuel]

        self.is_cathode = halfcell_dict['is_cathode']
        # anode is false; Cathode is true
        self.calc_act_loss = halfcell_dict['calc_act_loss']
        self.calc_cl_diff_loss = halfcell_dict['calc_cl_diff_loss']
        self.calc_gdl_diff_loss = halfcell_dict['calc_gdl_diff_loss']

        self.th_gdl = halfcell_dict['th_gdl']
        # thickness of the gas diffusion layer
        self.th_bpp = halfcell_dict['th_bpp']
        # thickness of the bipolar plate
        self.th_cl = halfcell_dict['th_cl']
        # thickness of the catalyst layer
        self.th_gde = self.th_gdl + self.th_cl
        # thickness gas diffusion electrode

        bpp_layer_dict = \
            {'thickness': halfcell_dict['th_bpp'],
             'width': self.width_straight_channels,
             'length': self.length_straight_channels,
             'electrical conductivity':
                 cell_dict['electrical conductivity bpp'],
             'thermal conductivity':
                 cell_dict['thermal conductivity bpp']}
        # 'porosity': self.channel.cross_area * self.n_chl / (
        #             self.th_bpp * self.width)}
        self.bpp = layers.SolidLayer(bpp_layer_dict, self.channel.dx)
        gde_layer_dict = \
            {'thickness': halfcell_dict['th_gdl'] + halfcell_dict['th_cl'],
             'width': self.width_straight_channels,
             'length': self.length_straight_channels,
             'electrical conductivity':
                 cell_dict['electrical conductivity gde'],
             'thermal conductivity':
                 cell_dict['thermal conductivity gde']}
        # 'porosity':
        #    (self.th_gdl * halfcell_dict['porosity gdl']
        #     + self.th_cl * halfcell_dict['porosity cl'])
        #    / (self.th_gde + self.th_cl)}
        self.gde = layers.SolidLayer(gde_layer_dict, self.channel.dx)

        self.thickness = self.bpp.thickness + self.gde.thickness

        """voltage loss parameter, (Kulikovsky, 2013)"""
        self.vol_ex_cd = halfcell_dict['vol_ex_cd']
        # exchange current density
        self.prot_con_cl = halfcell_dict['prot_con_cl']
        # proton conductivity of the catalyst layer
        self.diff_coeff_cl = halfcell_dict['diff_coeff_cl']
        # diffusion coefficient of the reactant in the catalyst layer
        self.diff_coeff_gdl = halfcell_dict['diff_coeff_gdl']
        # diffusion coefficient of the reactant in the gas diffusion layer
        self.tafel_slope = halfcell_dict['tafel_slope']
        # tafel slope of the electrode
        self.i_sigma = np.sqrt(2. * self.vol_ex_cd * self.prot_con_cl
                               * self.tafel_slope)
        # could use a better name see (Kulikovsky, 2013) not sure if 2-D
        # exchange current densisty
        self.index_cat = n_nodes - 1
        # index of the first element with negative cell voltage
        self.i_cd_char = self.prot_con_cl * self.tafel_slope / self.th_cl
        # not sure if the name is ok, i_ca_char is the characteristic current
        # densisty, see (Kulikovsky, 2013)
        self.act_loss = np.zeros(n_ele)
        # activation voltage loss
        self.gdl_diff_loss = np.zeros(n_ele)
        # diffusion voltage loss at the gas diffusion layer
        self.cl_diff_loss = np.zeros(n_ele)
        # diffusion voltage loss at the catalyst layer
        self.v_loss = np.zeros(n_ele)
        # sum of the activation and diffusion voltage loss
        self.beta = np.zeros(n_ele)
        # dimensionless parameter

        self.break_program = False
        # boolean to hint if the cell voltage runs below zero
        # if HT-PEMFC True; if NT-PEMFC False
        self.stoi = halfcell_dict['stoichiometry']
        # stoichiometry of the reactant at the channel inlet
        self.p_drop_bends = 0.
        # pressure drop in the channel through bends
        self.w_cross_flow = np.zeros(n_ele)
        # cross water flux through the membrane
        # self.g_fluid = np.zeros(n_nodes)
        # heat capacity flow of the species mixture including fluid water
        # self.cp_fluid = np.zeros(n_nodes)
        # heat capacity of the species mixture including fluid water
        # self.mol_flow_liq_w = np.zeros(n_nodes)
        # molar liquid water flux
        # self.p = np.full(n_nodes, self.channel.p_out)
        # channel pressure
        self.cond_rate = np.zeros(n_nodes)
        self.cond_rate_ele = np.zeros(n_ele)
        # condensation rate of water
        self.humidity = np.zeros(n_nodes)
        # gas mixture humidity
        self.u = np.zeros(n_nodes)
        # channel velocity
        # self.fwd_mat = np.tril(np.full((n_ele, n_ele), 1.))
        # forward matrix
        # self.bwd_mat = np.triu(np.full((n_ele, n_ele), 1.))
        # backward matrix
        # self.mol_flow_total = np.zeros(n_nodes)
        # self.mass_flow_total = np.zeros(n_nodes)
        # self.mol_flow_gas_total = np.zeros(n_nodes)
        # self.mass_flow_gas_total = np.zeros(n_nodes)

        # # fluid mass flow
        # self.vol_flow_gas = np.zeros(n_nodes)
        # # molar flux of the gas phase
        # (0: Reactant, 1: Water, 2: Inert Species
        # self.mol_flow = np.full((self.n_species, n_nodes), 0.)
        # self.mol_flow_liq = np.array(self.mol_flow)
        # self.mol_flow_gas = np.array(self.mol_flow)
        # self.mass_flow = np.array(self.mol_flow)
        # self.mass_flow_gas = np.array(self.mol_flow)
        # self.mass_flow_liq = np.array(self.mol_flow)
        # self.gas_conc = np.array(self.mol_flow)
        # molar concentration of each species
        # self.mol_fraction = np.array(self.mol_flow)
        # self.mol_fraction_gas = np.array(self.mol_fraction)
        # # molar fraction of the species in the gas phase
        # self.mass_fraction = np.array(self.mol_fraction)
        # self.mass_fraction_gas = np.array(self.mass_fraction)



        # self.temp_fluid = np.full(n_nodes, self.channel.temp_in)
        # self.temp_fluid_ele = np.full(n_ele, self.channel.temp_in)
        # # temperature of the fluid in the channel
        # self.rho_gas = np.full(n_nodes, 1.)
        # # density of the gas phase
        # self.visc_gas = np.full(n_nodes, 1.e-5)
        # # viscosity of the gas phase
        #
        #
        # mass fraction of the species in the gas phase
        self.r_gas = np.full(n_nodes, 0.)
        # gas constant of the gas phase
        self.r_species = np.full(self.n_species, 0.)
        # gas constant of the species
        self.cp = np.array(self.mol_flow)
        # heat capacity of the species in the gas phase
        self.lambdas = np.array(self.mol_flow)
        # heat conductivity of the species in the gas phase
        self.visc = np.array(self.mol_flow)
        # viscosity of the species in the gas phase
        # self.temp_fluid_ele = np.zeros(n_ele)
        # element based temperature of the gas phase
        self.cp_gas = np.zeros(n_nodes)
        # heat capacity of the gas phase
        self.ht_coeff = np.zeros(n_ele)
        # convection coefficient between the gas phase and the channel
        self.k_ht_coeff = np.zeros(n_ele)
        # heat conductivity between the gas phase and the channel
        self.cp_gas_ele = np.zeros(n_ele)
        # element based heat capacity
        self.lambda_gas = np.zeros(n_nodes)
        self.lambda_gas_ele = np.zeros(n_ele)
        # heat conductivity of the gas phase
        self.Pr = np.zeros(n_ele)
        # prandtl number of the gas phase
        for i, item in enumerate(self.mol_mass):
            self.r_species[i] = g_par.constants['R'] / item

        self.print_data = [
            {
                'Fluid Temperature': {'value': self.temp_fluid, 'units': 'K'}
            },
            {
                'Mol Fraction': {self.species_names[i]:
                                 {'value': self.mol_fraction[i], 'units': '-'}
                                 for i in range(len(self.mol_fraction))},
                'Mol Flow': {self.species_names[i]:
                             {'value': self.mol_flow[i], 'units': 'mol/s'}
                             for i in range(len(self.mol_fraction))},
                'Gas Mol Fraction':
                    {self.species_names[i]:
                     {'value': self.mol_fraction_gas[i], 'units': '-'}
                     for i in range(len(self.mol_fraction_gas))},
                'Gas Mol Flow':
                    {self.species_names[i]:
                     {'value': self.mol_flow_gas[i], 'units': 'mol/s'}
                     for i in range(len(self.mol_flow_gas))}
            }]

    def update(self, current_density):
        """
        This function coordinates the program sequence
        """
        # self.calc_temp_fluid_ele()
        self.calc_mass_balance(current_density)
        if not self.break_program:
            self.calc_cond_rates()
            self.calc_species_properties()
            self.calc_gas_properties()
            self.calc_flow_velocity()
            self.calc_pressure()
            self.calc_humidity()
            self.calc_fluid_properties()
            self.calc_heat_transfer_coeff()
            self.update_voltage_loss(current_density)

    def calc_mass_balance(self, current_density):
        self.calc_fuel_flow(current_density)
        self.calc_water_flow(current_density)
        self.mol_flow[:] = np.maximum(self.mol_flow, 0.)
        self.mol_flow_total[:] = np.sum(self.mol_flow, axis=0)
        self.mol_fraction[:] = self.calc_fraction(self.mol_flow)
        self.mass_fraction[:] = \
            self.molar_to_mass_fraction(self.mol_fraction, self.mol_mass)
        self.calc_mass_flow()
        self.calc_concentrations()
        self.calc_two_phase_flow()

    def update_voltage_loss(self, current_density):
        self.calc_electrode_loss(current_density)

    # def set_layer_temperature(self, var):
    #     """
    #     This function sets the layer Temperatures,
    #     they can be obtained from the temperature system.
    #     """
    #     var = ip.interpolate_along_axis(np.array(var), axis=1,
    #                                     add_edge_points=True)
    #     if self.is_cathode:
    #         self.temp = np.array([var[0], var[1], var[2]])
    #     else:
    #         self.temp = np.array([var[0], var[1]])

    def calc_fuel_flow(self, current_density):
        """
        Calculates the reactant molar flow [mol/s]
        """
        faraday = g_par.constants['F']
        tar_cd = g_par.dict_case['tar_cd']
        fuel_flow = \
            tar_cd * self.active_area * abs(self.n_stoi[self.id_fuel]) \
            / (self.n_charge * faraday) * self.stoi
        dfuel_flow = current_density * self.active_area_dx \
            * self.n_stoi[self.id_fuel] / (self.n_charge * faraday)
        g_func.add_source(self.mol_flow[self.id_fuel], dmol,
                          self.flow_direction)
        self.mol_flow[self.id_inert] = \
            self.mol_flow[self.id_fuel][self.ele_in] * self.inert_reac_ratio

    def calc_water_flow(self, current_density):
        """"
        Calculates the water molar flow [mol/s]
        """
        sat_p = w_prop.water.calc_p_sat(self.channel.temp_in)
        i_cd = current_density
        area = self.active_area_dx
        chl = self.channel
        q_0_water = \
            (self.mol_flow[self.id_fuel][self.ele_in]
             + self.mol_flow[self.id_inert][self.ele_in]) \
            * sat_p * chl.humidity_in \
            / (self.p[self.ele_in] - chl.humidity_in * sat_p)
        h2o_in = q_0_water
        h2o_source = np.zeros_like(i_cd)
        h2o_prod = area * self.n_stoi[self.id_h2o] * i_cd \
            / (self.n_charge * g_par.constants['F'])
        h2o_source += h2o_prod
        h2o_cross = area * self.w_cross_flow * self.flow_direction
        h2o_source += h2o_cross
        self.mol_flow[self.id_h2o] = h2o_in
        g_func.add_source(self.mol_flow[self.id_h2o],
                          h2o_source, self.flow_direction)

    def calc_mass_flow(self):
        """
        Calculates the relevant mass flows
        """
        self.mass_flow[:] = (self.mol_flow.transpose()
                             * self.mol_mass).transpose()
        self.mass_flow_total[:] = np.sum(self.mass_flow, axis=0)

    def calc_pressure(self):
        """
        Calculates the total channel pressure for each element.
        """
        chl = self.channel
        rho_ele = ip.interpolate_1d(self.rho_gas)
        u_ele = ip.interpolate_1d(self.u)
        reynolds = self.rho_gas * chl.d_h * self.u / self.visc_gas
        reynolds_ele = ip.interpolate_1d(reynolds)
        zeta_bends = chl.zeta_bends * chl.n_bends / self.n_ele
        friction_factor = 64.0 / reynolds_ele
        dp = (friction_factor * chl.dx / chl.d_h + zeta_bends) \
            * rho_ele * 0.5 * u_ele ** 2.0
        pressure_direction = -self.flow_direction
        self.p.fill(chl.p_out)
        g_func.add_source(self.p, dp, pressure_direction)

    @staticmethod
    def molar_to_mass_fraction(mol_fraction, mol_mass):
        """
        Calculates the mass fraction from molar fractions and molar masses.
        Molar fractions must be a (multi-dimensional) array with species
        along the first (0th) axis. Molar masses must be a one-dimensional
        array with the different species molar masses.
        """
        x_mw = mol_fraction.transpose() * mol_mass
        return x_mw.transpose() / np.sum(x_mw, axis=1)

    @staticmethod
    def calc_fraction(species_flow):
        """
        Calculates the species mixture fractions based on a multi-dimensional
        array with different species along the first (0th) axis.
        """
        return species_flow / np.sum(species_flow, axis=0)

    def calc_concentrations(self):
        """
        Calculates the gas phase molar concentrations.
        """
        # id_reac = 0
        # id_h2o = 1
        # id_inert = 2

        gas_constant = g_par.constants['R']
        total_mol_conc = self.p / (gas_constant * self.temp_fluid)
        conc = total_mol_conc * self.mol_fraction
        p_sat = w_prop.water.calc_p_sat(self.temp_fluid)
        sat_conc = p_sat / (gas_constant * self.temp_fluid)
        dry_air_mol_flow = np.copy(self.mol_flow)
        dry_air_mol_flow[self.id_h2o] = 0.0
        dry_air_fraction = self.calc_fraction(dry_air_mol_flow)
        self.gas_conc[:] = conc
        self.gas_conc[self.id_fuel] = \
            np.where(self.gas_conc[self.id_h2o] > sat_conc,
                     (total_mol_conc - sat_conc)
                     * dry_air_fraction[self.id_fuel],
                     self.gas_conc[self.id_fuel])
        self.gas_conc[self.id_inert] = \
            np.where(self.gas_conc[self.id_h2o] > sat_conc,
                     (total_mol_conc - sat_conc)
                     * dry_air_fraction[self.id_inert],
                     self.gas_conc[self.id_inert])
        self.gas_conc[self.id_h2o] = \
            np.where(self.gas_conc[self.id_h2o] > sat_conc,
                     sat_conc, self.gas_conc[self.id_h2o])
        self.gas_conc[:] = np.maximum(self.gas_conc, 1e-6)

    def calc_two_phase_flow(self):
        """
        Calculates the condensed phase flow and updates mole and mass fractions
        """
        self.mol_flow_liq[:] *= 0.0
        gas_conc_fuel = np.maximum(self.gas_conc[self.id_fuel], 1e-6)
        self.mol_flow_liq[self.id_h2o] = self.mol_flow[self.id_h2o] \
            - self.gas_conc[self.id_h2o] / gas_conc_fuel \
            * self.mol_flow[self.id_fuel]
        self.mass_flow_liq[:] *= 0.0
        self.mass_flow_liq[self.id_h2o] = \
            self.mol_flow_liq[self.id_h2o] * self.mol_mass[self.id_h2o]
        self.mol_flow_gas[:] = self.mol_flow - self.mol_flow_liq
        self.mass_flow_gas[:] = self.mass_flow - self.mass_flow_liq
        self.mol_flow_gas_total[:] = np.sum(self.mol_flow_gas, axis=0)
        self.mass_flow_gas_total[:] = np.sum(self.mass_flow_gas, axis=0)
        self.mol_fraction_gas[:] = self.calc_fraction(self.mol_flow_gas)
        self.mass_fraction_gas[:] = self.calc_fraction(self.mass_flow_gas)

    def calc_species_properties(self):
        """
        Calculates the properties of the species in the gas phase
        """
        for i in range(len(self.species)):
            self.cp[i] = self.species[i].calc_cp(self.temp_fluid)
            self.lambdas[i] = \
                self.species[i].calc_lambda(self.temp_fluid, self.p)
            self.visc[i] = self.species[i].calc_visc(self.temp_fluid)
        # if self.is_cathode:
        #     self.cp[self.id_reac] = g_prop.oxygen.calc_cp(self.temp_fluid)
        #     self.lambdas[self.id_reac] = \
        #         g_prop.oxygen.calc_lambda(self.temp_fluid, self.p)
        #     self.visc[self.id_reac] = g_prop.oxygen.calc_visc(self.temp_fluid)
        # else:
        #     self.cp[self.id_reac] = g_prop.hydrogen.calc_cp(self.temp_fluid)
        #     self.lambdas[self.id_reac] = \
        #         g_prop.hydrogen.calc_lambda(self.temp_fluid, self.p)
        #     self.visc[self.id_reac] = g_prop.hydrogen.calc_visc(self.temp_fluid)
        # self.cp[self.id_h2o] = g_prop.water.calc_cp(self.temp_fluid)
        # self.cp[self.id_inert] = g_prop.nitrogen.calc_cp(self.temp_fluid)
        # self.lambdas[self.id_h2o] = \
        #     g_prop.water.calc_lambda(self.temp_fluid, self.p)
        # self.lambdas[self.id_inert] = \
        #     g_prop.nitrogen.calc_lambda(self.temp_fluid, self.p)
        # self.visc[self.id_h2o] = g_prop.water.calc_visc(self.temp_fluid)
        # self.visc[self.id_inert] = g_prop.nitrogen.calc_visc(self.temp_fluid)

    # def calc_gas_properties(self):
    #     """
    #     Calculates the properties of the gas phase
    #     """
    #     self.cp_gas[:] = \
    #         np.sum(self.mass_fraction_gas * self.cp, axis=0)
    #     self.cp_gas_ele[:] = ip.interpolate_1d(self.cp_gas)
    #     self.visc_gas[:] = \
    #         g_func.calc_visc_mix(self.visc, self.mol_fraction_gas,
    #                              self.mol_mass)
    #     self.lambda_gas[:] = \
    #         g_func.calc_lambda_mix(self.lambdas, self.mol_fraction_gas,
    #                                self.visc, self.mol_mass)
    #     self.lambda_gas_ele[:] = ip.interpolate_1d(self.lambda_gas)
    #     self.r_gas[:] = \
    #         np.sum(self.mass_fraction_gas.transpose() * self.r_species, axis=1)
    #     self.rho_gas[:] = g_func.calc_rho(self.p, self.r_gas,
    #                                       self.temp_fluid)
        # self.Pr = self.visc_gas * self.cp_gas / self.lambda_gas

    # def calc_flow_velocity(self):
    #     """
    #     Calculates the gas phase velocity.
    #     The gas phase velocity is taken to be the liquid water velocity as well.
    #     """
    #     self.vol_flow_gas[:] = self.mass_flow_gas_total / self.rho_gas
    #     self.u[:] = self.vol_flow_gas / self.channel.cross_area

    # def calc_fluid_properties(self):
    #     """
    #     Calculate the fluid flow properties
    #     """
    #     cp_liq = g_par.dict_case['cp_liq']
    #     self.cp_fluid[:] = \
    #         ((self.mass_flow_total - self.mass_flow_gas_total) * cp_liq
    #          + self.mass_flow_gas_total * self.cp_gas) / self.mass_flow_total
    #     self.g_fluid[:] = self.mass_flow_total * self.cp_fluid

    def calc_heat_transfer_coeff(self):
        """
        Calculates convection coefficient and corresponding conductance
        between the channel wall and the fluid.
        """
        nusselt = 3.66
        chl = self.channel
        self.ht_coeff[:] = self.lambda_gas_ele * nusselt / chl.d_h
        self.k_ht_coeff[:] = \
            self.ht_coeff * chl.dx * 2.0 * (chl.width + chl.height)

    def calc_activation_loss(self, current_density, reac_conc_ele,
                             reac_conc_in):
        """
        Calculates the activation voltage loss,
        according to (Kulikovsky, 2013).
        """
        try:
            self.act_loss[:] = self.tafel_slope \
                * np.arcsinh((current_density / self.i_sigma) ** 2.
                             / (2. * (reac_conc_ele / reac_conc_in)
                                * (1. - np.exp(-current_density /
                                               (2. * self.i_cd_char)))))
        except FloatingPointError:
            print(current_density)
            raise

    def calc_transport_loss_catalyst_layer(self, current_density, var,
                                           reac_conc_ele):
        """
        Calculates the diffusion voltage loss in the catalyst layer
        according to (Kulikovsky, 2013).
        """
        i_hat = current_density / self.i_cd_char
        short_save = np.sqrt(2. * i_hat)
        beta = short_save / (1. + np.sqrt(1.12 * i_hat) * np.exp(short_save))\
            + np.pi * i_hat / (2. + i_hat)
        self.cl_diff_loss[:] = \
            ((self.prot_con_cl * self.tafel_slope ** 2.)
             / (4. * g_par.constants['F']
                * self.diff_coeff_cl * reac_conc_ele)
             * (current_density / self.i_cd_char
                - np.log10(1. + np.square(current_density) /
                           (self.i_cd_char ** 2. * beta ** 2.)))) / var

    def calc_transport_loss_diffusion_layer(self, var):
        """
        Calculates the diffusion voltage loss in the gas diffusion layer
        according to (Kulikovsky, 2013).
        """
        self.gdl_diff_loss[:] = -self.tafel_slope * np.log10(var)
        nan_list = np.isnan(self.gdl_diff_loss)
        if nan_list.any():
            self.gdl_diff_loss[np.argwhere(nan_list)[0, 0]:] = 1.e50

    def calc_electrode_loss(self, current_density):
        """
        Calculates the full voltage losses of the electrode
        """
        faraday_constant = g_par.constants['F']
        reac_conc_ele = ip.interpolate_1d(self.gas_conc[self.id_fuel])
        if self.flow_direction == 1:
            reac_conc_in = self.gas_conc[self.id_fuel, :-1]
        else:
            reac_conc_in = self.gas_conc[self.id_fuel, 1:]

        i_lim = 4. * faraday_constant * reac_conc_in \
            * self.diff_coeff_gdl / self.th_gdl
        var = 1. - current_density / i_lim * reac_conc_in / reac_conc_ele

        self.calc_activation_loss(current_density, reac_conc_ele, reac_conc_in)
        self.calc_transport_loss_catalyst_layer(current_density, var,
                                                reac_conc_ele)
        self.calc_transport_loss_diffusion_layer(var)
        if not self.calc_gdl_diff_loss:
            self.gdl_diff_loss[:] = 0.
        if not self.calc_cl_diff_loss:
            self.cl_diff_loss[:] = 0.
        if not self.calc_act_loss:
            self.act_loss[:] = 0.
        self.v_loss[:] = self.act_loss + self.cl_diff_loss + self.gdl_diff_loss
