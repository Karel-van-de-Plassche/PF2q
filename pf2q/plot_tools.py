#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module defines a standard style to plot stuff with PF2q. These are very
optional and in general poorly tested functions.
@author: Karel van de Plassche
@licence: GPLv3
"""
import matplotlib
import numpy as np
import matplotlib.pyplot as plt

import pf2q.tools as tools


def create_single_axis_figure(figure_name=""):
    if figure_name is "":
        N_figures = len([manager.canvas.figure
          for manager in matplotlib._pylab_helpers.Gcf.get_all_fig_managers()])
        fig = plt.figure("grid" + str(N_figures))
    else:
        fig = plt.figure(figure_name)

    ax = fig.add_subplot(111)
    return ax


def plot_grid(ax, x_map):
    """
    Plot a x_map grid on an ax. Plots lines with constant theta green, lines
    with constant psi red, and the triangulation blue.
    """
    ax.set_aspect(1)
    plot_points = np.append(x_map.points_x,
                            [x_map.points_x[0, :, :]], axis=0)
    plot_points[:, :, 0] += x_map.O[0]
    plot_points[:, :, 1] += x_map.O[1]

    # plot lines with constant psi red
    ax.plot(plot_points[:, :, 0],
            plot_points[:, :, 1], c='r')

    # plot lines with constant theta green
    ax.plot(np.transpose(plot_points[:, :, 0]),
            np.transpose(plot_points[:, :, 1]), c='g')

    # plot points themselves blue
    ax.scatter(x_map.points_x[:, :, 0] + x_map.O[0],
               x_map.points_x[:, :, 1] + x_map.O[1], c='b', s=10)

    # plot triangulation blue
    diag_plot = x_map.points_x.copy()
    for i in xrange(diag_plot.shape[0]):
        diag_plot[i, :, 0] = np.roll(x_map.points_x[i, :, 0], i, axis=0)
        diag_plot[i, :, 1] = np.roll(x_map.points_x[i, :, 1], i, axis=0)
    for j in xrange(diag_plot.shape[1]):
        diag_plot[:, j, 0] = np.roll(diag_plot[:, j, 0], - (j + 1), axis=0)
        diag_plot[:, j, 1] = np.roll(diag_plot[:, j, 1], - (j + 1), axis=0)

    ax.plot(diag_plot[:, :, 0] + x_map.O[0],
            diag_plot[:, :, 1] + x_map.O[1], c='c')
    ax.plot(diag_plot[:, :, 0] + x_map.O[0],
            diag_plot[:, :, 1] + x_map.O[1], c='c')

    # plot centroids purple
#    ax.scatter(x_map.G[:, :, 0] + x_map.O[0], x_map.G[:, :, 1] + x_map.O[1], color='p')
#    ax.scatter(x_map.H[:, :, 0] + x_map.O[0], x_map.H[:, :, 1] + x_map.O[1], colot='p')

    # format axes
    ax.set_ylabel("$Z [m]$")
    ax.set_xlabel("$R [m]$")
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=3))
    formatter = matplotlib.ticker.ScalarFormatter()
    formatter.set_powerlimits((-1, 1))
    ax.xaxis.set_major_formatter(formatter)




def plotyy(x_dataset, y_dataset, y_limits=([0, 0], [0, 0], [0, 0]),
           colors=('Blue', 'Green', 'Red', 'Cyan'),
           markers=('1', '2', '3', '4'),
           x_axis_label="",
           y_labels=("One", "Two", "Three", "Four"),
           y_axis_label=(""),
           figure_name="", title="", multiy=False,
           legend_loc="upper right"):
    """A standard way to plot data using only one x-axis."""
    if y_dataset.__class__ is not list:
        raise Exception("present y data in list")
    if x_dataset.__class__ is not list:
        x_dataset = np.tile(x_dataset, (len(y_dataset), s1))

    if figure_name is "":
        fig = plt.figure()
    else:
        fig = plt.figure(figure_name)
    ax = fig.add_subplot(111)
    axes = [ax]
    if multiy:
        if len(y_dataset) == 2:
            axes = [ax, ax.twinx()]
        elif len(y_dataset) == 3:
            axes = [ax, ax.twinx(), ax.twinx()]
            fig.subplots_adjust(right=0.75)
            axes[-1].spines['right'].set_position(('axes', 1.2))
            axes[-1].set_frame_on(True)
            axes[-1].patch.set_visible(False)

        for ax, color, marker, x, label, data, y_limit in zip(axes, colors, markers, x_dataset, y_labels, y_dataset, y_limits):
            ax.plot(x, data, marker=marker, color=color)
            ax.set_ylabel(label, color=color)
            ax.tick_params(axis='y', colors=color)
            if np.any(np.array(y_limit) != 0):
                ax.set_ylim(y_limit)

    elif not multiy:
        for color, marker, x, label, data in zip(colors, markers, x_dataset, y_labels, y_dataset):
            ax.plot(x, data, marker=marker, color=color, label=label)
            handles, labels = ax.get_legend_handles_labels()
            ax.legend(handles, labels, loc=legend_loc)
            ax.set_ylabel(y_axis_label)

    if title != "":
        plt.suptitle(title)
    axes[0].set_xlabel(x_axis_label)


def plot_estimate_q(finesse_output, B_theta, B_theta_est, B_phi, B_phi_est, q, q_est):
    B_theta_est_int, dl = finesse_output.x_map.contour_integral(B_theta_est)
    B_phi_est_int, _ = finesse_output.x_map.contour_integral(B_phi_est)

    B_theta_int, _ = finesse_output.x_map.contour_integral(B_theta)
    B_phi_int, _ = finesse_output.x_map.contour_integral(B_phi)

    L = np.sum(dl, axis=0)
    B_phi_int /= L
    B_theta_int /= L
    B_theta_est_int /= L
    B_phi_est_int /= L
    psi = finesse_output.psi_finesse[0, :]
    plotyy(psi, [abs(q), abs(q_est)],
           y_labels=["out", "est"], legend_loc="upper left",
           figure_name="q")
    plotyy(psi, [tools.relative_error(q, q_est)],
           y_labels=["rel error"], legend_loc="upper left",
           figure_name="q err")

    plotyy(psi, [abs(B_theta_int), abs(B_theta_est_int)],
           y_labels=["out", "est"], legend_loc="upper left",
           figure_name="B_theta")
    plotyy(psi, [tools.relative_error(B_theta_int, B_theta_est_int)],
           y_labels=["rel error"], legend_loc="upper left",
           figure_name="B_theta err")

    plotyy(psi, [abs(B_phi_int), abs(B_phi_est_int)],
           y_labels=["out", "est"], legend_loc="upper left",
           figure_name="B_phi")
    plotyy(psi, [tools.relative_error(B_phi_int, B_phi_est_int)],
           y_labels=["rel error"], legend_loc="upper left",
           figure_name="B_phi err")