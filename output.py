import numpy as np
import matplotlib.pyplot as plt
import os
import errno
import system.interpolation as ip
import input.geometry as geom
import shutil
import data.global_parameters as g_par
import system.global_functions as g_func
import system.stack as stack
import system.output_object as oo
from itertools import cycle, islice


class Output:

    def __init__(self, dict_output):
        self.save_csv = dict_output['save_csv']
        # switch to save the csv data
        self.save_plot = dict_output['save_plot']
        # switch to save the plot data
        self.show_loss = dict_output['show_loss']
        # switch to show the single voltage losses in the u-i-graph
        self.delimiter = ','
        self.csv_format = '%.9e'
        # object of the class Stack
        self.output_dir = os.path.join(os.path.dirname(__file__), 'output')

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            # shutil.rmtree(self.output_dir, ignore_errors=True)

    @staticmethod
    def clean_directory(directory):
        for file in os.listdir(directory):
            file_path = os.path.join(directory, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path, ignore_errors=True)
            except Exception as e:
                print(e)

    @staticmethod
    def set_ax_properties(ax, **kwargs):
        fontsize = kwargs.get('fontsize', 16)
        if 'xlabel' in kwargs:
            ax.set_xlabel(kwargs['xlabel'], fontsize=fontsize)
        if 'ylabel' in kwargs:
            ax.set_ylabel(kwargs['ylabel'], fontsize=fontsize)
        if 'margins' in kwargs:
            ax.margins(x=kwargs['margins'][0], y=kwargs['margins'][1])
        if 'xlim' in kwargs:
            ax.set_xlim(kwargs['xlim'])
        if 'ylim' in kwargs:
            ax.set_ylim(kwargs['ylim'])
        if 'xticks' in kwargs:
            ax.set_xticks(kwargs['xticks'])
        if 'yticks' in kwargs:
            ax.set_yticks(kwargs['yticks'])
        if 'labels' in kwargs:
            ax.legend(kwargs['labels'], fontsize=fontsize)
        if 'title' in kwargs:
            ax.set_title(kwargs['title'], fontsize=fontsize)
        return ax

    def plot_lines(self, ax, x, y, colormap=None, **kwargs):
        x = np.asarray(x)
        y = np.asarray(y)
        ny = len(y)

        if x.ndim != y.ndim:
            if x.ndim == 1:
                x = np.tile(x, (ny, 1))
            else:
                raise ValueError('Outer dimension of x is not one and not '
                                 'equal to outer dimension of y')
        if y.ndim == 1:
            ax.plot(x, y, marker=kwargs.get('marker', '.'),
                    markersize=kwargs.get('markersize', 5.0),
                    fillstyle=kwargs.get('fillstyle', 'full'),
                    linewidth=kwargs.get('linewidth', 1.0),
                    linestyle=kwargs.get('linestyle', '-'),
                    color=kwargs.get('color', 'k'))
        else:
            if colormap is not None:
                cmap = plt.get_cmap(colormap)
                colors = cmap(np.linspace(0.0, 1.0, ny))
            else:
                colors = \
                    kwargs.get('color',
                               list(islice(cycle(['k', 'b', 'r', 'g', 'y']),
                                           ny)))
            linestyles = \
                list(islice(cycle(kwargs.get('linestyle', ['-'])), ny))
            markers = \
                list(islice(cycle(kwargs.get('marker', ['.'])), ny))
            fillstyles = \
                list(islice(cycle(kwargs.get('fillstyle', ['full'])), ny))
            for i in range(ny):
                ax.plot(x[i], y[i], marker=markers[i],
                        markersize=kwargs.get('markersize', 5.0),
                        fillstyle=fillstyles[i],
                        linewidth=kwargs.get('linewidth', 1.0),
                        linestyle=linestyles[i],
                        color=colors[i])
        ax.grid(True)
        ax.use_sticky_edges = False
        ax.autoscale()
        ax.set_xscale(kwargs.get('xscale', 'linear'))
        ax.set_yscale(kwargs.get('yscale', 'linear'))
        ax = self.set_ax_properties(ax, **kwargs)
        return ax

    def create_figure(self, filepath, x_array, y_array, xlabels, ylabels,
                      xlims=None, ylims=None, xticks=None, yticks=None,
                      titles=None, rows=1, cols=1, **kwargs):
        nplots = rows*cols

        def check_dims(variable, correct_single_dim=False):
            if isinstance(variable, str):
                variable = [variable]
            if not isinstance(variable, (list, tuple, np.ndarray)):
                raise TypeError('variable must be provided '
                                'as tuple, list or numpy array')
            if len(variable) != nplots:
                if correct_single_dim:
                    if nplots == 1:
                        variable = [variable]
                    else:
                        raise ValueError('variable must be sequence with '
                                         'length equivalent to number of plots')
                else:
                    raise ValueError('variable must be sequence with '
                                     'length equivalent to number of plots')
            return variable

        if rows > 2:
            figsize = kwargs.get('figsize', (6.4, 4.8*float(rows)/2.0))
        else:
            figsize = kwargs.get('figsize', (6.4, 4.8))
        fig = plt.figure(dpi=kwargs.get('dpi', 150), figsize=figsize)

        x_array = np.asarray(x_array)
        y_array = check_dims(np.asarray(y_array), correct_single_dim=True)

        if len(x_array) != nplots:
            if x_array.ndim == 1:
                x_array = np.tile(x_array, (nplots, 1))
            else:
                raise ValueError('Dimension of x-array is not one and does not '
                                 'match number of plot')
        fontsize = kwargs.get('fontsize', 16)
        xlabels = check_dims(xlabels)
        ylabels = check_dims(ylabels)

        for i in range(nplots):
            ax = fig.add_subplot(rows, cols, i+1)
            ax = self.plot_lines(ax, x_array[i], y_array[i],
                                 xlabel=xlabels[i], ylabel=ylabels[i], **kwargs)
            if titles is not None:
                titles = check_dims(titles)
                ax.set_title(titles[i], fontsize=fontsize)
            if 'legend' in kwargs:
                legend = check_dims(kwargs['legend'], correct_single_dim=True)
                ax.legend(legend[i])
            if xlims is not None:
                xlims = check_dims(xlims, correct_single_dim=True)
                ax.set_xlim(xlims[i])
            if ylims is not None:
                xlims = check_dims(xlims, correct_single_dim=True)
                ax.set_ylim(ylims[i])
            if xticks is not None:
                xticks = check_dims(xticks, correct_single_dim=True)
                ax.set_xticks(xticks[i])
            if yticks is not None:
                xlims = check_dims(yticks, correct_single_dim=True)
                ax.set_yticks(yticks[i])
        plt.tight_layout()
        if filepath:
            fig.savefig(filepath, format=kwargs.get('fileformat', 'png'))
        return fig

    @staticmethod
    def plot(y_values, y_label, x_label, y_scale, colors,
             title, xlim_low, xlim_up, labels, path):
        if labels is not None:
            for i in range(len(y_values)):
                plt.plot(y_values[i], color=colors[i],
                         marker='.', label=labels[i])
        else:
            for i in range(len(y_values)):
                plt.plot(y_values[i], color=colors[i], marker='.')

        plt.xlabel(x_label, fontsize=16)
        plt.ylabel(y_label, fontsize=16)
        plt.yscale(y_scale)
        plt.tick_params(labelsize=14)
        plt.xlim(xlim_low, xlim_up)
        plt.tight_layout()
        plt.grid()
        if labels is not None:
            plt.legend()
        plt.savefig(os.path.join(path, title + '.png'))
        plt.close()

    @staticmethod
    def x_plot(path, x, y, x_label, y_label, x_scale='linear',
               y_scale='linear', xlim=None, ylim=None, title=None, labels=None):
        if labels is not None:
            for i in range(len(y)):
                plt.plot(x, y[i],
                         color=plt.cm.coolwarm(i / len(y)),
                         marker='.', label=labels[i])
        else:
            for i in range(len(y)):
                plt.plot(x, y[i],
                         color=plt.cm.coolwarm(i / len(y)), marker='.')

        plt.xlabel(x_label, fontsize=16)
        plt.ylabel(y_label, fontsize=16)
        plt.xscale(x_scale)
        plt.yscale(y_scale)
        plt.tick_params(labelsize=14)
        plt.autoscale(tight=True, axis='both', enable=True)
        if xlim is not None:
            plt.xlim(xlim[0], xlim[1])
        if ylim is not None:
            plt.ylim(ylim[0], ylim[1])
        plt.tight_layout()
        plt.grid()
        if labels is not None:
            plt.legend()
        plt.savefig(os.path.join(path, title + '.png'))
        plt.close()

    def write_array_to_csv(self, file_path, array,
                           header=None, separator_lines=None):
        with open(file_path, 'a') as file:
            if header is not None:
                file.write('# ' + header + '\n')
            if separator_lines is not None:
                for i in range(len(separator_lines)):
                    a = array[i]
                    if a.ndim == 1:
                        a = a.reshape(1, a.shape[0])
                    file.write(separator_lines[i])
                    np.savetxt(file, a,
                               delimiter=self.delimiter, fmt=self.csv_format)
            else:
                np.savetxt(file, array,
                           delimiter=self.delimiter, fmt=self.csv_format)
        return file

    def save(self, folder_name, fc_stack):
        if not self.save_csv and not self.save_plot:
            return None

        if not isinstance(fc_stack, stack.Stack):
            raise TypeError

        csv_path = os.path.join(self.output_dir, folder_name, 'csv_data')
        plot_path = os.path.join(self.output_dir, folder_name, 'plots')
        if not os.path.exists(csv_path):
            os.makedirs(csv_path)
        else:
            self.clean_directory(csv_path)
        if not os.path.exists(plot_path):
            os.makedirs(plot_path)
        # else:
        #    self.clean_directory(plot_path)

        def write_data(x_values, data_array, x_label, data_name,
                       units='-', colormap='coolwarm', **kwargs):
            file_name = data_name.replace(' ', '_')
            if self.save_plot:
                y_label = data_name + ' $[' + units + ']$'
                file_path = os.path.join(plot_path, file_name + '.png')
                self.create_figure(file_path, x_values, data_array, x_label,
                                   y_label, colormap=colormap, **kwargs)
            if self.save_csv:
                file_path = os.path.join(csv_path, file_name + '.csv')
                header = data_name + ' [' + units + ']'
                self.write_array_to_csv(file_path, data_array,
                                        header=header)

        def save_oo_collection(oo_collection, x_values, x_label, **kwargs):
            if not hasattr(oo_collection[0], 'print_data'):
                raise TypeError
            n_items = len(oo_collection)
            for name, content in oo_collection[0].print_data[0].items():
                value = content['value']
                var_array = g_func.construct_empty_stack_array(value, n_items)
                for i, item in enumerate(oo_collection):
                    var_array[i] = item.print_data[0][name]['value']
                x = x_values
                if var_array.shape[-1] == (len(x_values) - 1):
                    x = ip.interpolate_1d(x_values)
                write_data(x, var_array, x_label, name,
                           content['units'], **kwargs)

            for base_name, sub_dict in oo_collection[0].print_data[1].items():
                for sub_name, content in sub_dict.items():
                    value = content['value']
                    var_array = \
                        g_func.construct_empty_stack_array(value, n_items)
                    for i, item in enumerate(oo_collection):
                        var_array[i] = \
                            item.print_data[1][base_name][sub_name]['value']
                    x = x_values
                    if var_array.shape[-1] == (len(x_values) - 1):
                        x = ip.interpolate_1d(x_values)
                    name = sub_name + ' ' + base_name
                    write_data(x, var_array, x_label,
                               name, content['units'], **kwargs)

        # Save cell values
        cells = fc_stack.cells
        xvalues = cells[0].cathode.channel.x
        xlabel = 'Channel Location [m]'
        save_oo_collection(cells, xvalues, xlabel)

        # # Save half cell values
        # cathodes = [cell.cathode for cell in fc_stack.cells]
        # save_oo_collection(cathodes, xvalues, xlabel)
        # anodes = [cell.anode for cell in fc_stack.cells]
        # save_oo_collection(cathodes, xvalues, xlabel)

        # Save channel values
        cathode_channels = [cell.cathode.channel for cell in fc_stack.cells]
        save_oo_collection(cathode_channels, xvalues, xlabel)
        anode_channels = [cell.anode.channel for cell in fc_stack.cells]
        save_oo_collection(anode_channels, xvalues, xlabel)

        # Save fluid values
        cathode_fluids = [cell.cathode.channel.fluid for cell in fc_stack.cells]
        save_oo_collection(cathode_fluids, xvalues, xlabel)
        anode_fluids = [cell.anode.channel.fluid for cell in fc_stack.cells]
        save_oo_collection(anode_fluids, xvalues, xlabel)

        # Save fuel circuit values
        fuel_circuits = fc_stack.fuel_circuits
        xvalues = [i + 1 for i in range(len(cells))]
        xlabel = 'Cell'
        save_oo_collection(fuel_circuits, xvalues, xlabel,
                           legend=['Cathode', 'Anode'])

        # Save coolant circuit values
        coolant_circuits = [fc_stack.coolant_circuit]
        xvalues = [i + 1 for i in range(coolant_circuits[0].n_channels)]
        xlabel = 'Channel'
        save_oo_collection(coolant_circuits, xvalues, xlabel)

    def plot_polarization_curve(self, voltage_loss,
                                cell_voltages, target_current_density):
        """
        Plots the polarization curve of the given
        current densities and average stack voltages.
        """
        cd_array = np.asarray(target_current_density) * 1.e-4
        plt.plot(cd_array, cell_voltages, marker='.', color='k',
                 label='Simulation')
        if self.show_loss is True:
            plt.plot(cd_array, voltage_loss['membrane']['average'],
                     color='b', marker='.', label='Membrane Loss')
            plt.plot(cd_array, voltage_loss['activation']['anode']['average'],
                     color='g', marker='*', label='Anode Activation Loss')
            plt.plot(cd_array,
                     voltage_loss['activation']['cathode']['average'],
                     color='g', marker='+', label='Cathode Activation Loss')
            plt.plot(cd_array,
                     voltage_loss['diffusion']['CL']['anode']['average'],
                     color='y', marker='*', label='Anode CL Diff Loss')
            plt.plot(cd_array,
                     voltage_loss['diffusion']['CL']['cathode']['average'],
                     color='y', marker='+', label='Cathode CL Diff Loss')
            plt.plot(cd_array,
                     voltage_loss['diffusion']['GDL']['anode']['average'],
                     color='m', marker='*', label='Anode GDL Diff Loss')
            plt.plot(cd_array,
                     voltage_loss['diffusion']['GDL']['cathode']['average'],
                     color='m', marker='+', label='Cathode GDL Diff Loss')
        plt.ylabel('Voltage $[V]$', fontsize=16)
        plt.xlabel('Current Density $[A/cm²]$', fontsize=16)
        plt.tick_params(labelsize=14)
        plt.grid()
        plt.legend()
        plt.autoscale(tight=True, axis='both', enable=True)
        plt.ylim(0., 1.)
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'polarization_curve.png'))
        plt.close()
