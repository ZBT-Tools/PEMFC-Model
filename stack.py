import numpy as np
import copy
import matrix_database as m_d
import saturation_pressure_vapour as p_sat
import input_parameter as i_p
import global_functions as g_func
import global_parameter as g_par
import cell as cl


class Stack:

    def __init__(self, dict):
        self.cell_numb = dict['cell_numb']
        self.heat_pow = dict['heat_power']
        self.resistivity = dict['plate_res']
        self.heigth = dict['heigth']
        self.width = dict['width']
        self.kf = dict['dis_dis_fac']
        self.stoi_cat = dict['stoi_cat']
        self.stoi_ano = dict['stoi_ano']
        self.alpha_f_conv = g_par.dict_case['conv_coef']
        self.cool_ch_bc = dict['cool_ch_bc']
        self.h_col = dict['h_col']
        self.m_col = dict['m_flow_col']
        self.cp_col = dict['cp_col']
        self.alpha_cool = dict['alpha_cool']
        self.cell_list =[]
        for i in range(self.cell_numb):
            x = cl.Cell(i_p.cell)
            self.cell_list.append(x)
        self.init_func()
        self.init_arrays()
        self.init_param()

    def init_func(self):
        #if self.stoi_ano <= 1.1 or self.stoi_cat <= 1.1:
         #   g_par.dict_case['tar_cd'] = g_par.dict_case['tar_cd'] * min(self.stoi_cat, self.stoi_ano)
          #  self.stoi_cat = self.stoi_cat * 1.2 / min(self.stoi_cat, self.stoi_ano)
           # self.stoi_ano = self.stoi_ano * 1.2 / min(self.stoi_cat, self.stoi_ano)
            #print('tar_cd:', g_par.dict_case['tar_cd'], self.stoi_ano)
        self.g_cool = self.m_col * self.cp_col
        if self.cool_ch_bc is False:
            self.t = np.full((self.cell_numb, g_par.dict_case['nodes']),
                                 i_p.t_cool_in)
            self.a_cool = np.full(self.cell_numb, self.alpha_cool)
            self.a_cool[0] = 1.e-20
        else:
            self.a_cool = np.full(self.cell_numb+1, self.alpha_cool)
            self.t = np.full((self.cell_numb+1, g_par.dict_case['nodes']),
                                 i_p.t_cool_in)
        self.extent = 2. * (self.width + self.heigth)
        self.cross_area = self.width * self.heigth
        self.h_d = 4. * self.cross_area / self.extent
        self.q_h_in_cat = np.full(self.cell_numb, 0.)
        self.q_h_in_ano = np.full(self.cell_numb, 0.)
        self.q_h_in_cat[-1] = self.stoi_cat \
                             * self.cell_numb \
                             * g_par.dict_case['tar_cd'] \
                             * np.average(self.cell_list[0].cathode.channel.width) \
                             * np.average(self.cell_list[0].cathode.channel.length) \
                             / (4. * g_par.dict_uni['f']) \
                             * (1. + self.cell_list[-1].cathode.n2o2ratio) \
                             * (1. + self.cell_list[-1].cathode.channel.phi
                                * p_sat.water.calc_psat(self.cell_list[-1].cathode.channel.t_in)
                                / self.cell_list[-1].cathode.channel.p_in
                                   - self.cell_list[-1].cathode.channel.phi
                                   * p_sat.water.calc_psat(self.cell_list[-1].cathode.channel.t_in))
        self.q_h_in_ano[-1] = self.stoi_ano \
                             * self.cell_numb \
                             * g_par.dict_case['tar_cd'] \
                             * self.cell_list[-1].anode.channel.width \
                             * self.cell_list[-1].anode.channel.length \
                             / (2. * g_par.dict_uni['f']) \
                             * (1. + self.cell_list[-1].anode.channel.phi
                                * p_sat.water.calc_psat(self.cell_list[-1].anode.channel.t_in)
                                / (self.cell_list[-1].anode.channel.p_in
                                   - self.cell_list[-1].anode.channel.phi
                                   * p_sat.water.calc_psat(self.cell_list[-1].anode.channel.t_in)))
        self.set_stoi(np.full(self.cell_numb, self.stoi_cat),
                      np.full(self.cell_numb, self.stoi_ano))

    def init_param(self):
        #n_col = int(self.cell_list[0].cathode.channel.width
         #           / self.cell_list[0].cathode.thickness_plate)
        n_col = 1
        self.d_col = 4. * (self.cell_list[0].cathode.channel.width * self.h_col)\
                     / (2. * (self.h_col + self.cell_list[0].cathode.channel.width))
        self.r_alpha_col = 1./(self.a_cool * np.pi * self.cell_list[0].cathode.channel.d_x * self.d_col)
        self.r_alpha_col = 1. / (n_col * 1. / self.r_alpha_col)
        #print(self.r_alpha_col)

    def init_arrays(self):
        x = np.full(g_par.dict_case['nodes']-1, g_par.dict_case['tar_cd'])
        y = []
        for q in range(self.cell_numb): y.append(x)
        self.i = np.array(y)
        self.q_h_out_cat = np.full(self.cell_numb, 0.)
        self.q_h_out_ano = np.full(self.cell_numb, 0.)
        self.t_h_out_cat = np.full(self.cell_numb, 0.)
        self.t_h_out_ano = np.full(self.cell_numb, 0.)
        self.r_mix_h_in_cat = np.full(self.cell_numb, 0.)
        self.r_mix_h_out_cat = np.full(self.cell_numb, 0.)
        self.r_mix_h_in_ano = np.full(self.cell_numb, 0.)
        self.r_mix_h_out_ano = np.full(self.cell_numb, 0.)
        self.p_h_in_cat = np.full(self.cell_numb, i_p.p_cat_in)
        self.p_h_out_cat = np.full(self.cell_numb, i_p.p_cat_in)
        self.p_h_out_ano = np.full(self.cell_numb, i_p.p_ano_in)
        self.p_h_in_ano = np.full(self.cell_numb, i_p.p_ano_in)
        self.q_x_cat = np.full(self.cell_numb,
                               self.q_h_in_cat[-1] / self.cell_numb)
        self.q_x_ano = np.full(self.cell_numb,
                               self.q_h_in_ano[-1] / self.cell_numb)
        self.b = m_d.b(g_par.dict_case['nodes']-1,
                       self.cell_numb,
                       self.cell_list[0].cathode.channel.d_x)
        self.c = m_d.c(g_par.dict_case['nodes']-1,
                       self.cell_numb,
                       self.cell_list[0].cathode.channel.d_x)
        self.stack_r()
        self.stack_resistance()
        self.zero = np.full(self.cell_numb, 0.)
        self.r_zero = np.full(self.cell_numb, 1.e50)
        self.r_alpha_gp = np.full(self.cell_numb, 0.)
        self.r_alpha_pp = np.full(self.cell_numb, 0.)
        self.r_alpha_gm = np.full(self.cell_numb, 0.)
        self.r_alpha_gegm = np.full(self.cell_numb, 0.)
        self.r_alpha_gegp = np.full(self.cell_numb, 0.)
        self.r_alpha_gepp = np.full(self.cell_numb, 0.)
        self.cool_m1 = m_d.col_mat_m1(g_par.dict_case['nodes'])
        fac = 1.
        for q, item in enumerate(self.cell_list):
            self.r_alpha_gp[q] = 2. / (self.alpha_f_conv
                                    * self.cell_list[q].cathode.channel.d_x
                                    * (self.cell_list[q].cathode.thickness_plate
                                       + self.cell_list[q].cathode.thickness_gde)) * fac
            self.r_alpha_gm[q] = 2. / (self.alpha_f_conv
                                    * self.cell_list[q].cathode.channel.d_x
                                    * (self.cell_list[q].cathode.thickness_plate
                                       + self.cell_list[q].thickness_mea)) * fac
            self.r_alpha_pp[q] = 1. / (self.alpha_f_conv
                                    * self.cell_list[q].cathode.channel.d_x
                                    * self.cell_list[q].cathode.thickness_plate) * fac
            self.r_alpha_gegm[q] = 2. / (self.alpha_f_conv
                                         * self.cell_list[q].cathode.channel.width
                                         * (self.cell_list[q].cathode.thickness_gde
                                            + self.cell_list[q].thickness_mea))
            self.r_alpha_gegp[q] = 2. / (self.alpha_f_conv
                                         * self.cell_list[q].cathode.channel.width
                                         * (self.cell_list[q].cathode.thickness_gde
                                            + self.cell_list[q].cathode.thickness_plate))
            self.r_alpha_gepp[q] = 1. / (self.alpha_f_conv
                                         * self.cell_list[q].cathode.channel.width
                                         * self.cell_list[q].cathode.thickness_plate)
        self.r_alpha_gegp = np.full(self.cell_numb, 1.e50)
        self.r_alpha_gegm = np.full(self.cell_numb, 1.e50)
        self.r_alpha_gepp = np.full(self.cell_numb, 1.e50)

    def update(self):
        for j in range(self.cell_numb):
            self.cell_list[j].set_i(self.i[j, :])
            self.cell_list[j].update()
        self.update_temperatur_coupling()
        self.update_flows()
        self.i_old = copy.deepcopy(self.i)
        self.update_electrical_coupling()

    def update_flows(self):
        self.sum_header_flows()
        self.calc_header_temp()
        self.calc_header_velocity()
        self.calc_header_r_mix()
        self.calc_header_roh()
        self.calc_header_reynolds_numb()
        self.calc_header_fanning_friction_factor()
        self.calc_header_p_out()
        self.calc_ref_p_drop()
        self.calc_ref_perm()
        self.calc_header_p_in()
        self.calc_flow_distribution_factor()
        self.calc_new_ref_p_drop()
        self.calc_header_p_in()
        self.calc_flow_distribution_factor()
        self.calc_new_cell_flows()
        self.calc_new_cell_stoi()
        self.set_stoi(self.new_stoi_cat, self.new_stoi_ano)
        self.set_p()

    def update_electrical_coupling(self):
        self.stack_v()
        self.stack_dv()
        self.calc_i()

    def update_temperatur_coupling(self):
        self.stack_alpha()
        self.calc_coolant_channel_t()
        self.calc_layer_t_orginal()
        #self.calc_gas_channel_t()

    def set_i(self, i):
        self.i = i

    def stack_resistance(self):
        d_p = []
        for q, item in enumerate(self.cell_list):
               d_p.append(self.cell_list[q].cathode.thickness_plate)
        self.resistance = self.resistivity / np.average(d_p)

    def stack_r(self):
        r_p, r_g, r_m = [], [], []
        r_pp, r_gp, r_gm = [], [], []
        for i, item in enumerate(self.cell_list):
            r_p = np.hstack((r_p, self.cell_list[i].r_p))
            r_g = np.hstack((r_g, self.cell_list[i].r_g))
            r_m = np.hstack((r_m, self.cell_list[i].r_m))
            r_pp = np.hstack((r_pp, self.cell_list[i].r_pp))
            r_gp = np.hstack((r_gp, self.cell_list[i].r_gp))
            r_gm = np.hstack((r_gm, self.cell_list[i].r_gm))
        self.r_m = r_m
        self.r_g = r_g
        self.r_p = r_p
        self.r_pp = r_pp
        self.r_gp = r_gp
        self.r_gm = r_gm

    def stack_alpha(self):
        r_alpha_cat, r_alpha_ano = [], []
        for i, item in enumerate(self.cell_list):
            r_alpha_cat = np.hstack((r_alpha_cat, self.cell_list[i].cathode.r_ht_coef_a))
            r_alpha_ano = np.hstack((r_alpha_ano, self.cell_list[i].anode.r_ht_coef_a))
        #self.r_alpha_cat = r_alpha_cat
        self.r_alpha_cat = np.full(self.cell_numb, 1.e50)
        #self.r_alpha_ano = r_alpha_ano
        self.r_alpha_ano = np.full(self.cell_numb, 1.e50)

    def stack_v(self):
        var = []
        for i, item in enumerate(self.cell_list):
            var = np.hstack((var, self.cell_list[i].v))
        self.v = var
        # running

    def stack_dv(self):
        var = []
        for i, item in enumerate(self.cell_list):
            var = np.hstack((var, self.cell_list[i].dv))
        self.dv = var

    def set_stoi(self, stoi_cat, stoi_ano):
        for q in range(self.cell_numb):
            self.cell_list[q].cathode.stoi = stoi_cat[q]
            self.cell_list[q].anode.stoi = stoi_ano[q]

    def calc_stoi(self, q, val):
        if val is 4:
            b = 1 + self.cell_list[-1].cathode.n2o2ratio
            c = 1 + self.cell_list[-1].cathode.channel.phi \
                * p_sat.water.calc_psat(self.cell_list[-1].cathode.channel.t_in) \
                / (self.cell_list[-1].cathode.channel.p_in
                   - self.cell_list[-1].cathode.channel.phi
                   * p_sat.water.calc_psat(self.cell_list[-1].cathode.channel.t_in))
            a = g_par.dict_case['tar_cd']\
                * self.cell_list[-1].cathode.channel.width\
                * self.cell_list[-1].cathode.channel.heigth\
                / (val * g_par.dict_uni['f'])
        else:
            c = 1. + self.cell_list[-1].anode.channel.phi \
                * p_sat.water.calc_psat(self.cell_list[-1].anode.channel.t_in) \
                / (self.cell_list[-1].anode.channel.p_in
                   - self.cell_list[-1].anode.channel.phi
                   * p_sat.water.calc_psat(self.cell_list[-1].anode.channel.t_in))
            a = g_par.dict_case['tar_cd']\
                * self.cell_list[-1].anode.channel.width\
                * self.cell_list[-1].anode.channel.heigth\
                / (val * g_par.dict_uni['f'])
        return q /(a * b * c)

    def set_p(self):
        for q in range(self.cell_numb):
            self.cell_list[q].cathode.channel.p_in = self.p_h_in_cat[q]
            self.cell_list[q].anode.channel.p_in = self.p_h_in_ano[q]

    def sum_header_flows(self): # ok change here for parallel flow
        self.q_h_in_cat[0] = self.cell_list[0].cathode.q_sum[0]
        self.q_h_out_cat[0] = self.cell_list[0].cathode.q_sum[-1]
        self.q_h_in_ano[0] = self.cell_list[0].anode.q_sum[-1]
        self.q_h_out_ano[0] = self.cell_list[0].anode.q_sum[0]
        for q in range(1, self.cell_numb):
            self.q_h_in_cat[q] = self.q_h_in_cat[q - 1] \
                                 + self.cell_list[q].cathode.q_sum[0]
            self.q_h_out_cat[q] = self.q_h_out_cat[q - 1] \
                                  + self.cell_list[q].cathode.q_sum[-1]
            self.q_h_in_ano[q] = self.q_h_in_ano[q - 1] \
                                 + self.cell_list[q].anode.q_sum[-1]
            self.q_h_out_ano[q] = self.q_h_out_ano[q - 1] \
                                  + self.cell_list[q].anode.q_sum[0]

    def calc_header_temp(self):
        self.t_h_out_cat[0] = self.cell_list[0].cathode.t_gas[-1]
        self.t_h_out_ano[0] = self.cell_list[0].anode.t_gas[0]
        for q in range(1, self.cell_numb):
            self.t_h_out_cat[q] = (self.t_h_out_cat[q - 1] * self.q_h_out_cat[q - 1]
                                   + self.cell_list[q].cathode.q_sum[-1]
                                   * self.cell_list[q].cathode.t2[-1]) \
                                  / self.q_h_out_cat[q]
            self.t_h_out_ano[q] = (self.t_h_out_ano[q - 1] * self.q_h_out_ano[q - 1]
                                   + self.cell_list[q].anode.q_sum[0]
                                   * self.cell_list[q].anode.t2[0]) \
                                  / self.q_h_out_ano[q]

    def calc_header_velocity(self):
        self.v_h_in_cat = self.q_h_in_cat \
                          * g_par.dict_uni['r'] \
                          * self.cell_list[-1].cathode.channel.t_in \
                          / (self.p_h_in_cat * self.cross_area)
        self.v_h_in_ano = self.q_h_in_ano \
                          * g_par.dict_uni['r'] \
                          * self.cell_list[-1].anode.channel.t_in \
                          / (self.p_h_in_ano * self.cross_area)
        self.v_h_out_cat = self.q_h_out_cat \
                           * g_par.dict_uni['r'] \
                           * self.t_h_out_cat \
                           / (self.p_h_out_cat * self.cross_area)
        self.v_h_out_ano = self.q_h_out_ano \
                           * g_par.dict_uni['r'] \
                           * self.t_h_out_ano \
                           / (self.p_h_out_ano * self.cross_area)

    def calc_header_r_mix(self):
        self.r_mix_h_in_cat = np.full(self.cell_numb, self.cell_list[0].cathode.r_mix[0])
        self.r_mix_h_in_ano = np.full(self.cell_numb, self.cell_list[0].anode.r_mix[-1])
        self.r_mix_h_out_cat[0] = self.cell_list[0].cathode.r_mix[-1]
        self.r_mix_h_out_ano[0] = self.cell_list[0].anode.r_mix[0]
        for q in range(1, self.cell_numb):
            self.r_mix_h_out_cat[q] = (self.r_mix_h_out_cat[q - 1] * self.q_h_out_cat[q - 1]
                                       + self.cell_list[q].cathode.q_sum[-1]
                                       * self.cell_list[q].cathode.r_mix[-1]) \
                                      / self.q_h_out_cat[q]
            self.r_mix_h_out_ano[q] = (self.r_mix_h_out_ano[q - 1] * self.q_h_out_ano[q - 1]
                                       + self.cell_list[q].anode.q_sum[0]
                                       * self.cell_list[q].anode.r_mix[0]) \
                                      / self.q_h_out_ano[q]

    def calc_header_roh(self):
        self.roh_h_in_cat = g_func.calc_rho(self.p_h_in_cat,
                                            self.r_mix_h_in_cat,
                                            self.cell_list[-1].cathode.channel.t_in)
        self.roh_h_in_ano = g_func.calc_rho(self.p_h_in_ano,
                                            self.r_mix_h_in_ano,
                                            self.cell_list[-1].anode.channel.t_in)
        self.roh_h_out_cat = g_func.calc_rho(self.p_h_out_cat,
                                             self.r_mix_h_out_cat,
                                             self.t_h_out_cat)
        self.roh_h_out_ano = g_func.calc_rho(self.p_h_out_ano,
                                             self.r_mix_h_out_ano,
                                             self.t_h_out_ano)

    def calc_header_reynolds_numb(self):
        for q in range(self.cell_numb):
            self.re_h_in_cat = g_func.calc_re(self.roh_h_in_cat,
                                              self.v_h_in_cat,
                                              self.h_d,
                                              self.cell_list[q].cathode.visc_mix[0])
            self.re_h_in_ano = g_func.calc_re(self.roh_h_in_ano,
                                              self.v_h_in_ano,
                                              self.h_d,
                                              self.cell_list[q].anode.visc_mix[-1])
            self.re_h_out_cat = g_func.calc_re(self.roh_h_out_cat,
                                               self.v_h_out_cat,
                                               self.h_d,
                                               self.cell_list[q].cathode.visc_mix[-1])
            self.re_h_out_ano = g_func.calc_re(self.roh_h_out_ano,
                                               self.v_h_out_ano,
                                               self.h_d,
                                               self.cell_list[q].anode.visc_mix[0])

    def calc_header_fanning_friction_factor(self):
        self.f_h_in_cat = g_func.calc_fanning_friction_factor(self.re_h_in_cat)
        self.f_h_in_ano = g_func.calc_fanning_friction_factor(self.re_h_in_ano)
        self.f_h_out_cat = g_func.calc_fanning_friction_factor(self.re_h_out_cat)
        self.f_h_out_ano = g_func.calc_fanning_friction_factor(self.re_h_out_ano)

    def calc_header_p_out(self):  # change for parallel flow
        self.p_h_out_cat[self.cell_numb - 1] = g_par.dict_case['header_p_in_cat']
        self.p_h_out_ano[self.cell_numb - 1] = g_par.dict_case['header_p_in_ano']
        for q in range(self.cell_numb - 1, 0, -1):
            self.p_h_out_cat[q - 1] = self.p_h_out_cat[q] \
                                      + g_func.calc_header_pressure_drop(self.roh_h_out_cat[q-1],
                                                                         self.v_h_out_cat[q],
                                                                         self.v_h_out_cat[q-1],
                                                                         self.f_h_out_cat[q-1],
                                                                         self.kf,
                                                                         self.cell_list[q].heigth,
                                                                         self.h_d)
            self.p_h_out_ano[q - 1] = self.p_h_out_ano[q] \
                                      + g_func.calc_header_pressure_drop(self.roh_h_out_ano[q-1],
                                                                         self.v_h_out_ano[q],
                                                                         self.v_h_out_ano[q-1],
                                                                         self.f_h_out_ano[q-1],
                                                                         self.kf,
                                                                         self.cell_list[q].heigth,
                                                                         self.h_d)

    def calc_ref_perm(self):
        self.perm_ano = np.average(self.cell_list[0].anode.visc_mix)\
                        / self.cell_list[0].anode.channel.cross_area\
                        * self.cell_list[0].anode.channel.length\
                        * np.average(self.cell_list[0].anode.q_sum)\
                        / self.ref_p_drop_ano
        self.perm_cat = np.average(self.cell_list[0].cathode.visc_mix)\
                        / self.cell_list[0].cathode.channel.cross_area\
                        * self.cell_list[0].cathode.channel.length\
                        * np.average(self.cell_list[0].cathode.q_sum)\
                        / self.ref_p_drop_cat
        self.ref_p_new_drop_cat = np.average(self.cell_list[0].cathode.q_sum)\
                         / self.cell_list[0].cathode.channel.cross_area\
                         * np.average(self.cell_list[0].cathode.visc_mix)\
                         * self.cell_list[0].cathode.channel.length\
                         / self.perm_cat
        self.p_adjusting_factor_cat = self.ref_p_drop_cat / self.ref_p_new_drop_cat
        self.ref_p_new_drop_ano = np.average(self.cell_list[0].anode.q_sum)\
                         / self.cell_list[0].anode.channel.cross_area\
                         * np.average(self.cell_list[0].anode.visc_mix)\
                         * self.cell_list[0].anode.channel.length\
                         / self.perm_ano
        self.p_adjusting_factor_ano = self.ref_p_drop_ano / self.ref_p_new_drop_ano

    def calc_ref_p_drop(self):
        self.ref_p_drop_cat = self.cell_list[0].cathode.p[0]\
                              - self.cell_list[0].cathode.p[-1]
        self.ref_p_drop_ano = self.cell_list[0].anode.p[-1]\
                              - self.cell_list[0].anode.p[0]

    def calc_new_ref_p_drop(self):
        self.ref_p_drop_cat = self.q_h_in_cat[self.cell_numb-1]\
                              / np.sum(self.alpha_cat)\
                              * np.average(self.cell_list[0].cathode.visc_mix)\
                              * self.cell_list[0].cathode.channel.length\
                              / self.cell_list[0].cathode.channel.cross_area\
                              / self.perm_cat\
                              * self.p_adjusting_factor_cat
        self.ref_p_drop_ano = self.q_h_in_ano[self.cell_numb-1]\
                              / np.sum(self.alpha_ano)\
                              * np.average(self.cell_list[0].anode.visc_mix)\
                              * self.cell_list[0].anode.channel.length\
                              / self.cell_list[0].anode.channel.cross_area\
                              / self.perm_ano\
                              * self.p_adjusting_factor_ano

    def calc_header_p_in(self):
        self.p_h_in_cat[0] = self.ref_p_drop_cat + self.p_h_out_cat[0]
        self.p_h_in_ano[0] = self.ref_p_drop_ano + self.p_h_out_ano[0]
        for q in range(1, self.cell_numb):
            self.p_h_in_cat[q] = self.p_h_in_cat[q - 1] \
                                 + g_func.calc_header_pressure_drop(self.roh_h_in_cat[q],
                                                                    self.v_h_in_cat[q - 1],
                                                                    self.v_h_in_cat[q],
                                                                    self.f_h_in_cat[q],
                                                                    self.kf,
                                                                    self.cell_list[q].heigth,
                                                                    self.h_d)
            self.p_h_in_ano[q] = self.p_h_in_ano[q - 1] \
                                 + g_func.calc_header_pressure_drop(self.roh_h_in_ano[q],
                                                                    self.v_h_in_ano[q - 1],
                                                                    self.v_h_in_ano[q],
                                                                    self.f_h_in_ano[q],
                                                                    self.kf,
                                                                    self.cell_list[q].heigth,
                                                                    self.h_d)

    def calc_flow_distribution_factor(self):
        self.alpha_cat = (self.p_h_in_cat - self.p_h_out_cat)\
                         / self.ref_p_drop_cat
        self.alpha_ano = (self.p_h_in_ano - self.p_h_out_ano)\
                         / self.ref_p_drop_ano

    def calc_new_cell_flows(self):
        self.q_x_cat = (self.p_h_in_cat - self.p_h_out_cat)\
                        * self.perm_cat\
                        * self.cell_list[0].cathode.channel.cross_area\
                        / np.average(self.cell_list[0].cathode.visc_mix)\
                        / self.cell_list[0].cathode.channel.length\
                        / self.p_adjusting_factor_cat
        self.q_x_ano = (self.p_h_in_ano - self.p_h_out_ano) \
                       * self.perm_ano \
                       * self.cell_list[0].anode.channel.cross_area \
                       / np.average(self.cell_list[0].anode.visc_mix) \
                       / self.cell_list[0].anode.channel.length \
                       / self.p_adjusting_factor_ano

    def calc_new_cell_stoi(self):
        self.new_stoi_cat = self.q_x_cat /\
                            (self.q_h_in_cat[-1] / self.cell_numb)\
                            * self.stoi_cat
        self.new_stoi_ano = self.q_x_ano\
                            / (self.q_h_in_ano[-1] / self.cell_numb)\
                            * self.stoi_ano
        min_cat = np.amin(self.new_stoi_cat)
        min_ano = np.amin(self.new_stoi_ano)
        min_min = min(min_cat, min_ano)
        #print(min_cat, min_ano, min_min, 'min_min', g_par.dict_case['tar_cd'])
        #if min_min <= 1.1:
          #  stoi_fac = i_p.stoi_min / min_min
         #   g_par.dict_case['tar_cd'] = g_par.dict_case['tar_cd'] / stoi_fac
           # self.i = self.i / stoi_fac
           # print(self.new_stoi_cat, 'stoi_before_change')
           # self.new_stoi_cat = self.new_stoi_cat * stoi_fac
           # print(self.new_stoi_cat, 'stoi_after_change')
           # self.new_stoi_ano = self.new_stoi_ano * stoi_fac
           # self.stoi_ano = self.stoi_ano * stoi_fac
           # self.stoi_cat = self.new_stoi_cat * stoi_fac

    def calc_n(self):
        self.n = np.matmul(self.b, self.v) - self.resistance\
                 * np.matmul(self.c, self.i.flatten(order='C'))

    def calc_n_no_cp(self):
        self.n = np.matmul(self.b, self.v)

    def calc_g(self):
        self.s = np.diag(self.dv)
        self.g = self.b * self.s - self.resistance * self.c

    def calc_g_no_cp(self):
        self.s = np.diag(self.dv)
        self.g = self.b * self.s

    def correct_i(self):
        self.i = self.i / (np.average(self.i) / g_par.dict_case['tar_cd'])

    def correct_i_new(self):
        self.i[int(self.cell_numb/2)-1, -1] = g_par.dict_case['nodes']\
                        * g_par.dict_case['tar_cd']\
                        - np.sum(self.i[int(self.cell_numb/2) - 1]) + self.i[int(self.cell_numb/2) -1, -1]

    def correct_i_new_no_cp(self):
        for q, item in enumerate (self.cell_list):
            self.i[q, -1] = (g_par.dict_case['nodes']-1) * g_par.dict_case['tar_cd']\
                            - np.sum(self.i[q]) + self.i[q, -1]

    def calc_i(self):
        self.calc_n()
        self.calc_g()
        #self.calc_n_no_cp()
        #self.calc_g_no_cp()
        i_pre_cor = self.i_old.flatten() - np.linalg.tensorsolve(self.g, self.n)
        self.i = g_func.toarray(i_pre_cor,
                                self.cell_numb,
                                g_par.dict_case['nodes']-1)
        self.correct_i_new_no_cp()
        #print(self.i)

    def calc_gas_channel_t(self):
        for q, item in enumerate(self.cell_list):
            #print(self.cell_list[0].anode.m_reac_flow_delta)
            #print(self.cell_list[0].anode.m_flow)
            print(self.cell_list[q].cathode.t_gas)
            for w in range(1, g_par.dict_case['nodes']):
                #self.cell_list[q].cathode.t_gas[w] = (self.cell_list[q].cathode.cp_mix[w - 1] * self.cell_list[q].cathode.m_flow[w - 1] * self.cell_list[q].cathode.t_gas[w - 1] \
                 #                                    + (self.cell_list[q].t2e[w-1] - self.cell_list[q].cathode.t_gas[w - 1] * .5) / self.r_alpha_cat[q] +)\
                  #                                   / (self.cell_list[q].cathode.cp_mix[w] * self.cell_list[q].cathode.m_flow[w] + .5 / self.r_alpha_cat[q])
                #self.cell_list[q].cathode.t_gas[w] = (self.cell_list[q].cathode.t_gas[w-1] * self.cell_list[q].cathode.cp_mix[w-1] * self.cell_list[q].cathode.m_flow[w-1]
                 #                                     + .5 * self.cell_list[q].cathode.m_vap_water_flow_delta[w-1] * self.cell_list[q].cathode.t_gas[w-1] * self.cell_list[q].cathode.cp[1, w-1]
                  #                                    - .5 * self.cell_list[q].cathode.m_reac_flow_delta[w-1] * self.cell_list[q].cathode.t_gas[w-1] * self.cell_list[q].cathode.cp[0, w-1]
                   #                                   + 1./self.r_alpha_cat[q] * (self.cell_list[q].t2e[w-1] - self.cell_list[q].cathode.t_gas[w-1] * .5))\
                    #                                 / (self.cell_list[q].cathode.cp_mix[w] * self.cell_list[q].cathode.m_flow[w]
                     #                                   - .5 * self.cell_list[q].cathode.m_vap_water_flow_delta[w-1] * self.cell_list[q].cathode.cp[1, w]
                      #                                  + 0.5 * self.cell_list[q].cathode.m_reac_flow_delta[w-1] * self.cell_list[q].cathode.cp[0, w]
                       #                                 + .5 / self.r_alpha_cat[q])
                self.cell_list[q].cathode.t_gas[w] = (self.cell_list[q].cathode.t_gas[w-1] * self.cell_list[q].cathode.cp_mix[w-1] * self.cell_list[q].cathode.m_flow[0]
                                                      + 1./self.r_alpha_cat[q] * (self.cell_list[q].t2e[w-1] - self.cell_list[q].cathode.t_gas[w-1] * .5))\
                                                     / (self.cell_list[q].cathode.cp_mix[w] * self.cell_list[q].cathode.m_flow[0] + .5 / self.r_alpha_cat[q])
                print(self.r_alpha_cat)
                print(self.cell_list[q].cathode.m_flow)
                print(self.cell_list[q].cathode.cp_mix)


            #print(self.cell_list[q].cathode.t_gas)
           # for w in range(g_par.dict_case['nodes']-2, -1, -1):
            #    self.cell_list[q].anode.t_gas[w] = (self.cell_list[q].anode.cp_mix[w + 1] * self.cell_list[q].anode.m_flow[w + 1] * self.cell_list[q].anode.t_gas[w + 1] \
             #                                      + self.cell_list[q].anode.cpe[w] * self.cell_list[q].anode.m_reac_flow_delta[w] * self.cell_list[q].anode.t_gas[w + 1] * .5
              #                                      + (self.cell_list[q].t5e[w] - self.cell_list[q].anode.t_gas[w+1] * .5) / self.r_alpha_ano[q])\
               #                                    / (self.cell_list[q].anode.cp_mix[w] * self.cell_list[q].anode.m_flow[w]
                #                                      - self.cell_list[q].anode.cpe[w] * self.cell_list[q].anode.m_reac_flow_delta[w] * 0.5
                 #                                     + 0.5 / self.r_alpha_ano[q])
           # print(self.cell_list[q].anode.t_gas)
    def calc_coolant_channel_t(self):
        for q, item in enumerate(self.cell_list):
            var1 = 0.5/(self.r_alpha_col[q] * self.g_cool)
            for w in range(1, g_par.dict_case['nodes']):
                self.t[q,w] = (var1 * (self.cell_list[q].t3[w]
                                       + self.cell_list[q].t3[w-1]
                                       - self.t[q,w-1]) + self.t[q,w-1])\
                              / (1.+ var1)
        if self.cool_ch_bc is True:
            var1 = 0.5 / (self.r_alpha_col[self.cell_numb-1] * self.g_cool)
            for w in range(1,g_par.dict_case['nodes']):
                self.t[self.cell_numb, w] = (var1 * (self.cell_list[self.cell_numb-1].t5[w]
                                           + self.cell_list[self.cell_numb-1].t5[w-1]
                                           - self.t[self.cell_numb, w-1]) + self.t[self.cell_numb, w-1])\
                                  / (1.+ var1)

    def calc_layer_t(self):
        self.I = g_func.calc_nodes(self.i) * self.cell_list[0].cathode.channel.plane_dx
        temp_mat = m_d.t_mat_no_bc_col(g_par.dict_case['nodes'],
                                         self.cell_numb,
                                         self.r_g,
                                         self.r_m,
                                         self.r_p,
                                         self.r_gp,
                                         self.r_gm,
                                         self.r_pp,
                                         self.r_alpha_col,
                                         np.full(self.cell_numb, 1.e50),#self.r_alpha_cat,
                                         self.r_alpha_ano,
                                         self.r_alpha_gm,
                                         self.r_alpha_gp,
                                         self.r_alpha_pp,
                                         self.r_alpha_gegm,
                                         self.r_alpha_gegp,
                                         self.r_alpha_gepp,
                                         self.cool_ch_bc)
        r_side = []
        for q, item in enumerate(self.cell_list):
            for w in range(g_par.dict_case['nodes']):
                if w is 0 or w is g_par.dict_case['nodes']-1: # bc nodes
                    if q is 0:
                        r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w]*0.5
                                      + .5 /self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + .5 /self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.25
                                      +.5 /self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w]
                                       * self.I[q,w] * 0.5) * self.I[q,w] * 0.5
                                      +.5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].cathode.gamma[w]*0.5
                                      + .5/self.r_alpha_gp[q]*g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu']) #+ 1./self.r_alpha_cat[q]* self.cell_list[q].cathode.t_gas[w] * 0.5
                        if self.cool_ch_bc is True:
                            r_side.append(-self.heat_pow * .5
                                          - .5 / self.r_alpha_pp[q] * g_par.dict_case['tu']
                                          - 1. / self.r_alpha_gepp[q] * g_par.dict_case['tu']
                                          -.5 / self.r_alpha_col[q] * self.t[q, w] )
                        else:
                            r_side.append(-self.heat_pow * .5
                                          - .5/self.r_alpha_pp[q] * g_par.dict_case['tu']
                                          - 1./self.r_alpha_gepp[q] * g_par.dict_case['tu'])
                    elif q is self.cell_numb-1:
                        if self.cool_ch_bc is True:
                            r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w] * 0.5
                                          + self.heat_pow * .5
                                          + .5 / self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + .5 / self.r_alpha_gp[q] * g_par.dict_case['tu']
                                          + 1. / self.r_alpha_gegp[q] * g_par.dict_case['tu']
                                          + .5 / self.r_alpha_col[q] * self.t[q+1, w])
                        else:
                            r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w] * 0.5
                                          + self.heat_pow * .5
                                          + .5 / self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + .5 / self.r_alpha_gp[q] * g_par.dict_case['tu']
                                          + 1. / self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.25
                                      + .5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w] * 0.5
                                      + .5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]*0.5
                                      + .5/self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])#+ 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w]*0.5
                        r_side.append(-.5 / self.r_alpha_col[q] * self.t[q, w]
                                      - .5/self.r_alpha_pp[q] * g_par.dict_case['tu']
                                      - 1./self.r_alpha_gepp[q] * g_par.dict_case['tu'])
                    else:
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w]*0.5
                                      + .5/self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + .5/self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.25
                                      + .5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w] * 0.5
                                      +.5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]*0.5 #+ 1./self.r_alpha_cat[q]
                                     # * self.cell_list[q].cathode.t_gas[w] *0.5
                                      +.5/self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(-.5 / self.r_alpha_col[q] * self.t[q, w]
                                      - .5/self.r_alpha_pp[q] * g_par.dict_case['tu']
                                      - 1. / self.r_alpha_gepp[q] * g_par.dict_case['tu'])
                else:
                    if q is 0:
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w]
                                      + 1./self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + 1./self.r_alpha_gp[q] * g_par.dict_case['t_u'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.5
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w]
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].cathode.gamma[w]
                          + 1./self.r_alpha_gp[q] * g_par.dict_case['tu'])# + 1./self.r_alpha_cat[q]
                                     # * self.cell_list[q].cathode.t_gas[w]
                        if self.cool_ch_bc is True:
                            r_side.append(-self.heat_pow - 1. / self.r_alpha_pp[q] * g_par.dict_case['tu']
                                          - self.t[q,w] * 1./self.r_alpha_col[q])
                        else:
                            r_side.append(-self.heat_pow - 1./self.r_alpha_pp[q] * g_par.dict_case['tu'])
                    elif q is self.cell_numb-1:
                        if self.cool_ch_bc is True:
                            r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w] + self.heat_pow
                                          + 1./self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + 1./self.r_alpha_gp[q] * g_par.dict_case['t_u'] + self.t[q+1,w] * 1./self.r_alpha_col[q])
                        else:
                            r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w] + self.heat_pow
                                          + 1. / self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + 1. / self.r_alpha_gp[q] * g_par.dict_case['t_u'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.5
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w]
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]
                                      + 1./self.r_alpha_gp[q] * g_par.dict_case['tu'])#+ 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w]
                        r_side.append(-1. / self.r_alpha_col[q] * self.t[q, w]
                                      - 1./self.r_alpha_pp[q] * g_par.dict_case['tu'])
                    else:
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w]
                                      + 1./self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + 1./self.r_alpha_gp[q] * g_par.dict_case['t_u'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w]**2 * 0.5
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w]
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]
                                      + 1. / self.r_alpha_gp[q] * g_par.dict_case['tu'])#+ 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w]
                        r_side.append(-1. / self.r_alpha_col[q] * self.t[q, w]
                                      - 1./self.r_alpha_pp[q] * g_par.dict_case['tu'])
        #t_vec = np.linalg.tensorsolve(np.asarray(temp_mat), r_side)
        #t_vec = np.linalg.lstsq(np.asarray(temp_mat), r_side, rcond=None)
        t_vec = np.linalg.solve(np.asarray(temp_mat), r_side)
        counter = 0
        for q, item in enumerate(self.cell_list):
            for w in range(g_par.dict_case['nodes']):
                self.cell_list[q].t5[w] = t_vec[counter]
                self.cell_list[q].t4[w] = t_vec[counter + 1]
                self.cell_list[q].t1[w] = t_vec[counter + 2]
                self.cell_list[q].t2[w] = t_vec[counter + 3]
                self.cell_list[q].t3[w] = t_vec[counter + 4]
                counter = counter + 5
            self.cell_list[q].t5e = g_func.calc_elements(self.cell_list[q].t5)
            self.cell_list[q].t2e = g_func.calc_elements(self.cell_list[q].t2)

    def calc_layer_t_orginal(self):
        self.I = g_func.calc_nodes(self.i) * self.cell_list[0].cathode.channel.plane_dx
        temp_mat = m_d.t_mat_no_bc_col(g_par.dict_case['nodes'],
                                         self.cell_numb,
                                         self.r_g,
                                         self.r_m,
                                         self.r_p,
                                         self.r_gp,
                                         self.r_gm,
                                         self.r_pp,
                                         self.r_alpha_col,
                                         self.r_alpha_cat,
                                         self.r_alpha_ano,
                                         self.r_alpha_gm,
                                         self.r_alpha_gp,
                                         self.r_alpha_pp,
                                         self.r_alpha_gegm,
                                         self.r_alpha_gegp,
                                         self.r_alpha_gepp,
                                         self.cool_ch_bc)
        r_side = []
        for q, item in enumerate(self.cell_list):
            for w in range(g_par.dict_case['nodes']):
                if w is 0 or w is g_par.dict_case['nodes']-1: # bc nodes
                    if q is 0:
                        r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w]*0.5
                                      + .5 /self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + .5 /self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.25
                                      +.5 /self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w]
                                       * self.I[q,w] * 0.5) * self.I[q,w] * 0.5
                                      +.5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].cathode.gamma[w]*0.5
                                      + .5/self.r_alpha_gp[q]*g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'] + 1./self.r_alpha_cat[q]* self.cell_list[q].cathode.t_gas[w] * 0.5)
                        if self.cool_ch_bc is True:
                            r_side.append(-self.heat_pow * .5
                                          - .5 / self.r_alpha_pp[q] * g_par.dict_case['tu']
                                          - 1. / self.r_alpha_gepp[q] * g_par.dict_case['tu']
                                          -.5 / self.r_alpha_col[q] * self.t[q, w] )
                        else:
                            r_side.append(-self.heat_pow * .5
                                          - .5/self.r_alpha_pp[q] * g_par.dict_case['tu']
                                          - 1./self.r_alpha_gepp[q] * g_par.dict_case['tu'])
                    elif q is self.cell_numb-1:
                        if self.cool_ch_bc is True:
                            r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w] * 0.5
                                          + self.heat_pow * .5
                                          + .5 / self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + .5 / self.r_alpha_gp[q] * g_par.dict_case['tu']
                                          + 1. / self.r_alpha_gegp[q] * g_par.dict_case['tu']
                                          + .5 / self.r_alpha_col[q] * self.t[q+1, w])
                        else:
                            r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w] * 0.5
                                          + self.heat_pow * .5
                                          + .5 / self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + .5 / self.r_alpha_gp[q] * g_par.dict_case['tu']
                                          + 1. / self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.25
                                      + .5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w] * 0.5
                                      + .5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]*0.5
                                      + .5/self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'] + 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w]*0.5)
                        r_side.append(-.5 / self.r_alpha_col[q] * self.t[q, w]
                                      - .5/self.r_alpha_pp[q] * g_par.dict_case['tu']
                                      - 1./self.r_alpha_gepp[q] * g_par.dict_case['tu'])
                    else:
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w]*0.5
                                      + .5/self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + .5/self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.25
                                      + .5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w] * 0.5
                                      +.5/self.r_alpha_gm[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]*0.5
                                      + 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w] *0.5
                                      +.5/self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_gegp[q] * g_par.dict_case['tu'])
                        r_side.append(-.5 / self.r_alpha_col[q] * self.t[q, w]
                                      - .5/self.r_alpha_pp[q] * g_par.dict_case['tu']
                                      - 1. / self.r_alpha_gepp[q] * g_par.dict_case['tu'])
                else:
                    if q is 0:
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w]
                                      + 1./self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + 1./self.r_alpha_gp[q] * g_par.dict_case['t_u'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.5
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w]
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].cathode.gamma[w]
                          + 1./self.r_alpha_gp[q] * g_par.dict_case['tu'] + 1./self.r_alpha_cat[q]
                                      * self.cell_list[q].cathode.t_gas[w])
                        if self.cool_ch_bc is True:
                            r_side.append(-self.heat_pow - 1. / self.r_alpha_pp[q] * g_par.dict_case['tu']
                                          - self.t[q,w] * 1./self.r_alpha_col[q])
                        else:
                            r_side.append(-self.heat_pow - 1./self.r_alpha_pp[q] * g_par.dict_case['tu'])
                    elif q is self.cell_numb-1:
                        if self.cool_ch_bc is True:
                            r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w] + self.heat_pow
                                          + 1./self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + 1./self.r_alpha_gp[q] * g_par.dict_case['t_u'] + self.t[q+1,w] * 1./self.r_alpha_col[q])
                        else:
                            r_side.append(g_par.dict_uni['h_vap'] * self.cell_list[q].anode.gamma[w] + self.heat_pow
                                          + 1. / self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                          + 1. / self.r_alpha_gp[q] * g_par.dict_case['t_u'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w] ** 2 * 0.5
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w]
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]
                                      + 1./self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w])
                        r_side.append(-1. / self.r_alpha_col[q] * self.t[q, w]
                                      - 1./self.r_alpha_pp[q] * g_par.dict_case['tu'])
                    else:
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].anode.gamma[w]
                                      + 1./self.r_alpha_ano[q] * self.cell_list[q].anode.t_gas[w]
                                      + 1./self.r_alpha_gp[q] * g_par.dict_case['t_u'])
                        r_side.append(self.cell_list[q].omega_a[w] * self.I[q, w]**2 * 0.5
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append((g_par.dict_case['vtn'] - self.cell_list[q].v_th[w] - self.cell_list[q].omega_a[w] *
                                       self.I[q, w] * 0.5) * self.I[q, w]
                                      + 1./self.r_alpha_gm[q] * g_par.dict_case['tu'])
                        r_side.append(g_par.dict_uni['h_vap']*self.cell_list[q].cathode.gamma[w]
                                      + 1. / self.r_alpha_gp[q] * g_par.dict_case['tu']
                                      + 1./self.r_alpha_cat[q] * self.cell_list[q].cathode.t_gas[w])
                        r_side.append(-1. / self.r_alpha_col[q] * self.t[q, w]
                                      - 1./self.r_alpha_pp[q] * g_par.dict_case['tu'])
        #t_vec = np.linalg.tensorsolve(np.asarray(temp_mat), r_side)
        #t_vec = np.linalg.lstsq(np.asarray(temp_mat), r_side, rcond=None)
        t_vec = np.linalg.solve(np.asarray(temp_mat), r_side)
        counter = 0
        for q, item in enumerate(self.cell_list):
            for w in range(g_par.dict_case['nodes']):
                self.cell_list[q].t5[w] = t_vec[counter]
                self.cell_list[q].t4[w] = t_vec[counter + 1]
                self.cell_list[q].t1[w] = t_vec[counter + 2]
                self.cell_list[q].t2[w] = t_vec[counter + 3]
                self.cell_list[q].t3[w] = t_vec[counter + 4]
                counter = counter + 5
            self.cell_list[q].t5e = g_func.calc_elements(self.cell_list[q].t5)
            self.cell_list[q].t2e = g_func.calc_elements(self.cell_list[q].t2) #np.full(g_par.dict_case['nodes'], 350.)