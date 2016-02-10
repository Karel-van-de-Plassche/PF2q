#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains the visual tool of PF2q. Creating a GUI with matplotlib
is always a bit hackish, so a lot of functions could be more optimized.
@author: Karel van de Plassche
@licence: GPLv3
"""
from collections import OrderedDict
import sys

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec

import pf2q.finesse as finesse
import pf2q.tools as tools


class FpTool(object):
    """ Defines the default layout of the FpTool."""

    n_bad = 4         # Number of 'bad boxes' below the q plot
    n_slid = 10       # Number of sliders
    n_but = 4         # Number of buttons below the sliders plot
    legend_size = 12  # Size of the legends in the plots

    # Define the grid on which everything is plotted
    gs = GridSpec(11, 1)
    plt_gs = GridSpecFromSubplotSpec(8, 2, subplot_spec=gs[0:5, 0], hspace=1)
    plt_bd_gs = GridSpecFromSubplotSpec(1, n_bad, subplot_spec=plt_gs[-1, 0])
    below_plt_2_gs = GridSpecFromSubplotSpec(1, 3, subplot_spec=plt_gs[-1, -1])
    sliders_gs = GridSpecFromSubplotSpec(n_slid, 1, subplot_spec=gs[5:10, 0])
    buttons_gs = GridSpecFromSubplotSpec(1, n_but, subplot_spec=gs[10, 0])

    def _define_badness(self):
        """ Defines the badness text boxes and lines."""
        parts = self.parts
        parts["badness"] = OrderedDict()
        for i in range(self.n_but):
            ax = self.fig.add_subplot(self.plt_bd_gs[0, i])
            ax.axis('off')
            parts["badness"][i] = {"txt": ax.text(.5, .5, "%.2f" % 0.0,
                                                  horizontalalignment='center',
                                                  verticalalignment='center',
                                                  transform=ax.transAxes,
                                                  bbox=dict(edgecolor = "black",
                                                            facecolor = "white"))}
            parts["badness"][i]["ln"] = parts["q_est"]["axis"].axvline(x=0,
                                                                       c='r')

    def _define_estimate_q(self, ylim=(0,7)):
        """ Defines the estimate q plot
        Defines all the axes and lines in the 'estimate q' plot. Call the
        _draw_estimate_q function to draw on this plot.
        """
        parts = self.parts
        parts["q_est"] = OrderedDict()
        parts["q_est"]["axis"] = self.fig.add_subplot(self.plt_gs[0:-2, 0])
        parts["q_est"]["axis"].set_xlabel("$\\rho$")
        parts["q_est"]["axis"].set_xlim((0, 1))
        parts["q_est"]["axis"].set_ylabel("q")
        parts["q_est"]["axis"].set_ylim(ylim)

        parts["q_est"]["l_target"], = parts["q_est"]["axis"].plot([], [], 'b', label = "target")
        parts["q_est"]["l_finesse"], = parts["q_est"]["axis"].plot([], [],'g', label = "FINESSE")
        parts["q_est"]["l_finesse_est"], = parts["q_est"]["axis"].plot([], [],'c', label = "FINESSE est")
        parts["q_est"]["l_manual"], = parts["q_est"]["axis"].plot([], [],'r', label = "manual")

        parts["q_est"]["axis"].legend(loc="upper left",
                                      prop={'size': self.legend_size})

    def _draw_finesse_q(self):
        """ Draws lines after running of finesse
        Draws:
        l_finesse -- Line for finesses q output
        l_target -- Line for q target

        Needs (static per FINESSE run):
        self.rho -- Rho from FINESSE output
        self.q_finesse -- q from FINESSE output
        self.q_finesse_est -- q estimated from FINESSE output

        Needs (static):
        self.rho_target
        self.q_target
        """
        parts = self.parts
        parts["q_est"]["l_finesse"].set_xdata(self.rho)
        parts["q_est"]["l_finesse"].set_ydata(self.q_finesse)

        parts["q_est"]["l_target"].set_xdata(self.rho_target)
        parts["q_est"]["l_target"].set_ydata(self.q_target)

        parts["q_est"]["l_finesse_est"].set_xdata(self.rho)
        parts["q_est"]["l_finesse_est"].set_ydata(self.q_finesse_est)

    def _draw_estimate_q(self):
        """ Draws lines after estimation of q
        Draws:
        l_manual -- Line for user generated input file
        [i]["ln"] -- Lines for badness values
        [i]["txt"] -- Text for badness value

        Needs (static per FINESSE run):
        self.rho -- Rho from FINESSE output

        Needs (per q estimation):
        self.q_est

        Needs (static):
        self.rho_target
        self.q_target
        """
        parts = self.parts
        parts["q_est"]["l_manual"].set_xdata(self.rho)
        parts["q_est"]["l_manual"].set_ydata(abs(self.q_est))

        tot, (badness_list) = \
            tools.badness(self.rho_target,
                          abs(self.q_target),
                          self.rho, abs(self.q_est))

        for i, item in enumerate(badness_list[:-1]):
            parts["badness"][i]["ln"].set_xdata([self.rho[item[0]],
                                                 self.rho[item[0]]])
            parts["badness"][i]["txt"].set_text("%.2f" % item[1])

    def _estimate_q(self):
        """ Estimates q
        Estimates q

        Overwrites/updates:
        self.q_est
        self.I_encl_est
        self.beta
        self.betap

        Needs (static per FINESSE run):
        self.map
        self.p
        self.R0
        self.estimation_case
        """
        self.q_est, self.I_encl_est, (B_theta, B_phi) = \
                                 self.estimation_case.estimate_q(self.input)

        self.beta = finesse.calculate_beta(self.map,
                                           self.p,
                                           B_phi,
                                           self.R0)
        self.betap = finesse.calculate_betap(self.map,
                                             self.p,
                                             B_theta,
                                             self.R0)

    def _define_below_plt_2(self):
        """ Defines the beta text boxes
        Defines the beta Text boxes. Call the _draw_betas function to put
        text in these boxes.
        """
        parts = self.parts
        names = ["beta", "betap", "delta"]
        for i, name in enumerate(names):
            ax = self.fig.add_subplot(self.below_plt_2_gs[0, i])
            ax.axis('off')
            parts[name] = ax.text(.5, .5, "%.2f" % 0.0,
                                  horizontalalignment='center',
                                  verticalalignment='center',
                                  transform=ax.transAxes,
                                  bbox=dict(edgecolor="black",
                                            facecolor="white"))

    def _define_buttons(self):
        """ Defines the global button boxes.
        Attach event with _attach()
        """
        parts = self.parts
        parts["buttons"] = OrderedDict()

        ax = self.fig.add_subplot(self.buttons_gs[0, 0])
        parts["buttons"][1] = Button(ax, "rerun FINESSE")

        ax = self.fig.add_subplot(self.buttons_gs[0, 1])
        parts["buttons"][2] = Button(ax, "Save Input")

        ax = self.fig.add_subplot(self.buttons_gs[0, 2])
        parts["buttons"][3] = Button(ax, "Load Input")

        ax = self.fig.add_subplot(self.buttons_gs[0, 3])
        parts["buttons"][4] = Button(ax, "Switch Tool")

    def _run_finesse(self, session, input, finesse_output=None):
        """ Runs finesse

        Overwrites/updates:
            self.finesse_output
            self.rho
            self.psi
            self.q_finesse
            self.estimation_case
            self.q_finesse
            self.I_encl_finesse
            self.B_theta
            self.B_phi
            self.map
            self.p
            self.R0
        """
        self.input = input
        if finesse_output is None:
            finesse_output = self.finesse_output = session.run_finesse(input)
        else:
            self.finesse_output = finesse_output
        self.rho = finesse_output.calculate_rho()
        self.psi = finesse_output.psi_finesse[0, :]
        self.q_finesse = np.copy(abs(finesse_output.q_finesse[0, :]))

        # Let's determine our input parameters
        self.estimation_case = finesse_output.assume_dp_dF_correct()
        self.map = finesse_output.triangular_map
        self.p_finesse = np.copy(finesse_output.p)
        self.p = np.copy(finesse_output.p)
        self.R0 = finesse_output.R0

        self._estimate_q()

        self.q_finesse_est = np.copy(self.q_est)
        self.I_encl_finesse = np.copy(self.I_encl_est)

    def _rerun_finesse(self, event):
        self._run_finesse(self.session, self.input)
        self._draw_finesse_q()
        self._update_estimates(None)

    def __init__(self, session, first_input, asdexDataSet,
                 finesse_output=None, fig=None, input_path=None):
        if input_path is None:
            self.input_path = sys.argv[0]
        else:
            self.input_path = input_path
        #######################################################################
        # Import all data and run FINESSE and estimations once                #
        #######################################################################
        self.session = session
        self.parts = OrderedDict()
        if fig is None:
            self.fig = plt.figure()
        else:
            self.fig = fig

        self._define_estimate_q()
        self._define_badness()
        self._define_buttons()
        self._define_below_plt_2()

        self._run_finesse(session, first_input, finesse_output=finesse_output)

        self.I_encl_est = self.I_encl_finesse
        self.p = self.p_finesse

        self.target = asdexDataSet
        self.p_target = self.target.p_of_rho_lin
        self.q_target = self.target.q_of_rho_lin
        self.rho_target = self.target.rho_lin

        self.input = first_input
        self._draw_finesse_q()
        self._draw_estimate_q()

    def _save_input(self, event):
        self.input.save_input_dialog(initialdir=self.input_path)

    def _connect_button_events(self):
        self.parts["buttons"][1].on_clicked(self._update_finesse)
        self.parts["buttons"][2].on_clicked(self._save_input)

        self.parts["buttons"][3].on_clicked(self._load_input)
        self.parts["buttons"][4].on_clicked(self._switch_tool)

    def _switch_tool(self, event):
        # We need to keep a reference to prevent being garbage collected
        if 'tool' not in globals():
            global tool

        self.fig.clf()
        if self.__class__ == PTool:
            tool = FTool(self.session, self.input, self.target,
                         fig=self.fig, finesse_output=self.finesse_output)
        if self.__class__ == FTool:
            tool = PTool(self.session, self.input, self.target,
                         fig=self.fig, finesse_output=self.finesse_output)
        self.fig.canvas.draw()

    def _load_input(self, event, style="FINESSE"):
        try:
            input_dict = self.input.load_input_dialog(
                                              initialdir=self.input_path)
        except finesse.FinesseInput.FinesseInputError:
            print "No file selected"
        else:
            input_dict.update({"boundary": self.input.boundary})
            self.input = finesse.FinesseInput(input_dict, self.input.boundary,
                                              self.input.a_0,
                                              self.input.B_phi0)
            self._reset_sliders()
            self._update_estimates(None)

    def _read_sliders(self):
        """ Reads sliders
        Reads the changes in sliders and generates a new input file. Usually
        called every time a sliders changes

        Reads:
        sliders:
            F_*
            p_*
            alpha
            A_2

        Overwrites/updates:
        self.input:
            self.input.F2_tilde_poly
            self.input.P_tilde_poly
            self.input.alpha
            self.input.A_N[1]
        """
        for name, slider in self.parts["sliders"].items():
            if name.startswith("F_"):
                i = int(name.split("_")[-1])
                self.input.F2_tilde_poly[i] = slider.val
            elif name.startswith("p_"):
                i = int(name.split("_")[-1])
                self.input.P_tilde_poly[i] = slider.val
            elif name == "alpha":
                self.input.alpha = slider.val
            elif name == "A_2":
                self.input.A_N[1] = slider.val

    def _reset_sliders(self):
        for name, slider in self.parts["sliders"].iteritems():
            slider.poly.get_axes().cla()
        self._define_sliders()
        self.fig.canvas.draw()


class PTool(FpTool):
    def _update_estimates(self, val):
        self._read_sliders()
        self._estimate_q()
        self._recalculate_p()
        self._draw_estimate_q()
        self._draw_estimate_p()

    def _update_finesse(self, val):
        self._rerun_finesse(None)
        self._reset_sliders()
        self._draw_finesse_p()

    def _draw_finesse_p(self):
        self.parts["p"]["l_finesse"].set_xdata(self.rho)
        self.parts["p"]["l_finesse"].set_ydata(self.p_finesse)
        self.parts["p"]["l_target"].set_xdata(self.rho_target)
        self.parts["p"]["l_target"].set_ydata(self.p_target)
        self.parts["p"]["axis"].set_ylim(bottom=0,
                                         top=1.2 * max(self.p_finesse))

    def _draw_estimate_p(self):
        parts = self.parts
        parts["p"]["l_manual"].set_xdata(self.rho)
        parts["p"]["l_manual"].set_ydata(self.p)
        parts["beta"].set_text("%.2f" % (self.beta * 100) + "%")
        parts["betap"].set_text("%.2f" % (self.betap * 100) + "%")
        parts["delta"].set_text("%.2f" % sum(self.input.P_tilde_poly))

    def _recalculate_p(self):
        P_0 = self.estimation_case.P_0
        P_1 = self.estimation_case.P_1
        P = np.polyval(self.input.P_tilde_poly, self.psi)
        self.p = tools.rescale(P, P_0, P_1)

    def _connect_slider_events(self):
        for name, slider in self.parts["sliders"].iteritems():
            slider.on_changed(self._update_estimates)

    def _define_sliders(self):
        prefix = "p"
        self.parts["sliders"] = OrderedDict()
        for i in range(9):
            name = prefix + "_" + str(i)
            ax = self.fig.add_subplot(self.sliders_gs[i])
            slider = Slider(ax, name,
                            self.input.P_tilde_poly[i] - 0.5 * self.delta_p,
                            self.input.P_tilde_poly[i] + 0.5 * self.delta_p,
                            valinit=self.input.P_tilde_poly[i])
            self.parts["sliders"][name] = slider
        ax = self.fig.add_subplot(FpTool.sliders_gs[-1])
        self.parts["sliders"]["A_2"] = Slider(ax, "A_2", 0, self.delta_A_2,
                                              valinit=self.input.A_N[1])
        self._connect_slider_events()

    def _define_p(self):
        parts = self.parts
        parts["p"] = OrderedDict()
        parts["p"]["axis"] = self.fig.add_subplot(self.plt_gs[0:-2, 1])
        parts["p"]["axis"].set_xlabel("$\\rho$")
        parts["p"]["axis"].set_xlim((0, 1))
        parts["p"]["axis"].set_ylabel("$p$")
        parts["p"]["axis"].set_ylim((0, 1))
        parts["p"]["axis"].ticklabel_format(style='sci', axis='y',
                                            scilimits=(0, 0))

        parts["p"]["l_target"],  = parts["p"]["axis"].plot([], [], 'b', label="target")
        parts["p"]["l_finesse"], = parts["p"]["axis"].plot([], [], 'g', label="FINESSE")
        parts["p"]["l_manual"],  = parts["p"]["axis"].plot([], [], 'r', label="manual")

        parts["p"]["axis"].legend(loc="upper right", prop={'size': self.legend_size})

    def __init__(self, session, first_input, asdexDataSet,
                 finesse_output=None, fig=None, delta_p=1, delta_A_2=30,
                 input_path=None):
        FpTool.__init__(self, session, first_input, asdexDataSet,
                        finesse_output=finesse_output, fig=fig,
                        input_path=input_path)
        self.delta_p = delta_p
        self.delta_A_2 = delta_A_2
        self._define_sliders()
        self._define_p()

        self._connect_button_events()
        self._draw_finesse_p()
        self._draw_estimate_p()

class FTool(FpTool):
    def _update_estimates(self, val):
        self._read_sliders()
        self._estimate_q()
        self._draw_estimate_q()
        self._draw_I_encl_est()

    def _update_finesse(self, val):
        self._rerun_finesse(None)
        self._reset_sliders()
        self._draw_I_encl_finesse()

    def _connect_slider_events(self):
        for name, slider in self.parts["sliders"].iteritems():
            slider.on_changed(self._update_estimates)

    def _define_I_encl(self):
        parts = self.parts
        parts["I_encl"] = OrderedDict()
        parts["I_encl"]["axis"] = self.fig.add_subplot(self.plt_gs[0:-2, 1])
        parts["I_encl"]["axis"].set_xlabel("$\\rho$")
        parts["I_encl"]["axis"].set_xlim((0, 1))
        parts["I_encl"]["axis"].set_ylabel("$I_{encl}$")
        parts["I_encl"]["axis"].set_ylim((0, 1))
        parts["I_encl"]["axis"].ticklabel_format(style='sci', axis='y',
                                                 scilimits=(0, 0))

        parts["I_encl"]["l_finesse"], = parts["I_encl"]["axis"].plot([], [], 'g', label = "FINESSE")
        parts["I_encl"]["l_manual"],  = parts["I_encl"]["axis"].plot([], [], 'r', label = "manual")

        parts["I_encl"]["axis"].legend(loc = "lower right", prop={'size':self.legend_size})

    def _draw_I_encl_finesse(self):
        self.parts["I_encl"]["l_finesse"].set_xdata(self.rho)
        self.parts["I_encl"]["l_finesse"].set_ydata(self.I_encl_finesse)
        if self.I_encl_finesse[-1] > 0:
            self.parts["I_encl"]["axis"].set_ylim((0, 1.2 * max(self.I_encl_finesse)))
            self.parts["I_encl"]["axis"].legend(loc="lower right", prop={'size': self.legend_size})
        else:
            self.parts["I_encl"]["axis"].set_ylim(0, 1.2 * min(self.I_encl_finesse))
            self.parts["I_encl"]["axis"].legend(loc="upper right", prop={'size': self.legend_size})
        self.parts["delta"].set_text("%.2f" % sum(self.input.F2_tilde_poly))

    def _draw_I_encl_est(self):
        parts = self.parts
        parts["I_encl"]["l_manual"].set_xdata(self.rho)
        parts["I_encl"]["l_manual"].set_ydata(self.I_encl_est)

        parts["beta"].set_text("%.2f" % (self.beta * 100) + "%")
        parts["betap"].set_text("%.2f" % (self.betap * 100) + "%")
        parts["delta"].set_text("%.2f" % sum(self.input.F2_tilde_poly))

    def _define_sliders(self):
        prefix = "F"
        self.parts["sliders"] = OrderedDict()
        for i in range(9):
            name = prefix + "_" + str(i)
            ax = self.fig.add_subplot(self.sliders_gs[i])
            slider = Slider(ax, name,
                            self.input.F2_tilde_poly[i] - 0.5 * self.delta_F,
                            self.input.F2_tilde_poly[i] + 0.5 * self.delta_F,
                            valinit=self.input.F2_tilde_poly[i])
            self.parts["sliders"][name] = slider
        ax = self.fig.add_subplot(FpTool.sliders_gs[-1])
        self.parts["sliders"]["alpha"] = Slider(ax, "alpha", 0,
                                                self.delta_alpha,
                                                valinit=self.input.alpha)
        self._connect_slider_events()

    def __init__(self, session, first_input, asdexDataSet,
                 finesse_output=None, fig=None, delta_F=40, delta_alpha=8,
                 input_path=None):

        FpTool.__init__(self, session, first_input, asdexDataSet,
                        finesse_output=finesse_output, fig=fig,
                        input_path=input_path)

        self.delta_F = delta_F
        self.delta_alpha = delta_alpha
        self._define_sliders()
        self._define_I_encl()
        self._connect_button_events()

        self._draw_I_encl_finesse()
        self._draw_I_encl_est()


class CombiTool():
    def __init__(self, analyse_path, session, first_input, dry_filename, input_path=None):
        self.ftool = FTool(analyse_path, session, first_input, dry_filename)
        self.ptool = PTool(analyse_path, session, first_input, dry_filename)
