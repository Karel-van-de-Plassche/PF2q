# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 10:39:14 2015

@author: karel
"""
import sys
import matplotlib
#matplotlib.use('pdf')
#matplotlib.use('Qt4Agg')
matplotlib.use('TkAgg')
import numpy as np
import os
import shutil
#from scipy.io import savemat
from sys import platform
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
sys.path.append("/Users/Karel/Dropbox/PF2q")
sys.path.append("D:/Users/Karel/Dropbox/PF2q")
import pf2q.finesse as finesse
import pf2q.pf2qvis as fptool
import pf2q.asdex as asdex
import pf2q.tools as tools
import pf2q.plot_tools as plot_tools
import pickle
from mpl_toolkits.axes_grid1 import make_axes_locatable
# Ignore this..
#root = tk.Tk()
#root.withdraw()
#file_path = tkFileDialog.askopenfilename()

if __name__ == '__main__':
    # Stuff to make pretty pictures
    plot_style = "normal"
    matplotlib.rcParams['font.size'] = 20 
    matplotlib.rcParams["lines.markersize"] = 20
    matplotlib.rcParams["figure.dpi"] = 96
    # In inch
    #matplotlib.rcParams["figure.figsize"] = [12.0, 9.0]
    matplotlib.rcParams["text.usetex"] = True
    matplotlib.rcParams["mathtext.default"] = "regular"
    #\newcommand{\R}{\mathbb{R}}
    #matplotlib.rcParams["axes.formatter.use_mathtext"] = True
    matplotlib.rcParams["axes.formatter.limits"] = [-2, 2]
    matplotlib.rcParams["pgf.texsystem"] = r"pdflatex"
    matplotlib.rcParams["pgf.preamble"] = [r"\usepackage{siunitx}",
                                           r"\usepackage{commath}"]
  
    #plt.ticklabel_format(style='sci')
    # We divide by 0 quite often, so let's ignore this warming
    np.seterr(all="ignore")

    #%% Load and initialize input/target
    tex_path = "/Users/karel/Dropbox/report/Pictures/"
    finesse_case_path = "/Users/karel/FORT/FINESSE/finesse_/test_karel/"
    mode = "karel_remote"
#    session = finesse.FinesseSession(finesse_case_path)
#
    boundary = finesse.FinesseInput.read_boundary_file("boundary.dat")
    input = finesse.FinesseInput.read_input_file("finesse_backup.inp")
    target = asdex.AsdexDataSet.load_matlab("test_eq_AUG30382at2p5.mat")        
    
    
    #target_fig = target.plot("target")
    #target_fig.savefig(tex_path + 'target_profiles.pdf')
    finesse_input = finesse.FinesseInput(input, boundary, target.a_0, target.B_phi0)

    pkl_file = open('data_npoints.pkl', 'rb')
    results = pickle.load(pkl_file)
    pkl_file.close()
    
    #%% plot input profiles
    psi_lin = np.linspace(0, 1)
    input_fig = plt.figure("input")
    plt.subplot(211)
    plt.plot(psi_lin, finesse_input.A_N[0] * np.polyval(finesse_input.F2_tilde_poly, psi_lin))
    plt.xlabel("$\psi$")
    plt.ylabel("$\\tilde{F}$")
    plt.subplot(212)
    plt.plot(psi_lin, finesse_input.A_N[1] * np.polyval(finesse_input.P_tilde_poly, psi_lin))
    plt.xlabel("$\psi$")
    plt.ylabel(r"$\tilde{p}$")
    input_fig.savefig(tex_path + "input.pdf")
    
    #%% Plot time
    #time_fig = plt.figure("time")
    time_fig, (ax) = plt.subplots()
    npoints = [17, 33, 65, 129, 257]
    raw_time = {17: 0.4,
                33: 1.834,
                65: 14.142,
                129: 159.42,
                257: 2094.064}
    karel_time = {17: 0.000789399147034,
                  33: 0.00110407829285,
                  65: 0.00204279899597,
                  129: 0.00555768013,
                  257: 0.0205494403839}
    x_ = []
    y_ = []
    y2_ = []
    y3_ = []
    for npoint in npoints:
        x_.append(npoint)
        y_.append(results[npoint]["time"])
        y2_.append(raw_time[npoint])
        y3_.append(karel_time[npoint])
        
    #plt.semilogy(x_, y_, label = "FINESSE + import")
    plt.semilogy(x_, y_, label = "$FINESSE$")
    plt.semilogy(x_, y3_, label = "$PF2q$")
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(base=32))
    formatter = matplotlib.ticker.ScalarFormatter()
    formatter.set_powerlimits((-5,5))
    ax.xaxis.set_major_formatter(formatter)
    plt.xlim(xmax = 256+32)
    plt.xlabel(r"$N_R = N_t$")
    plt.ylabel(r"$t[s]$")
    plt.legend(loc = "upper left", fontsize = "small")
    #ax.xaxis.ticklabel_format(style='plain')
    time_fig.savefig(tex_path + 'time.pdf')
    
    #%% Estimate q
    finesse_output = results[33]["finesse_output"]
    finesse_output.B_p = finesse_output.B_theta
    psi = finesse_output.psi_finesse[0,:]
    finesse_output.estimate_from_output()
    
    estimation_case = finesse_output.assume_dp_dF_correct()
    q_est, I_encl, (B_p_est, B_phi_est) = estimation_case.estimate_q(finesse_input)
    
    
    #%% plot estimate q stuff
    #%% plot I_encl
    I_encl_fig = plt.figure("I_encl")
    plt.plot(psi, I_encl)
    plt.xlabel("$\psi$")
    plt.ylabel("$I_{encl}[A]$")
    I_encl_fig.savefig(tex_path + 'I_encl.pdf')

    #%% plot field error    
    B_theta_est_int, _ = finesse_output.triangular_map.contour_integral(B_p_est[:-1,:])
    B_theta_int, _ = finesse_output.triangular_map.contour_integral(finesse_output.B_p[:-1,:])
    B_theta_error = tools.relative_error(B_theta_int, B_theta_est_int)
    
    B_phi_est_int, _ = finesse_output.triangular_map.contour_integral(B_phi_est[:-1,:])
    B_phi_int, _ = finesse_output.triangular_map.contour_integral(finesse_output.B_phi[:-1,:])
    B_phi_error = tools.relative_error(B_phi_int, B_phi_est_int)
    
    field_error_fig = plt.figure("field_error")
    plt.subplot(211)
    plt.plot(psi, B_theta_error)
    plt.xlabel("$\psi$")
    plt.ylabel(r"$\eta_{B_p}$")
  
    plt.subplot(212)
    plt.plot(psi, B_phi_error)
    plt.xlabel("$\psi$")
    plt.ylabel("$\eta_{B_\phi}$")
    
    plt.tight_layout()
    
    field_error_fig.savefig(tex_path + 'field_error.pdf')
    
    #%% B_p fluctuation
    out = results[257]["finesse_output"]
    out.B_p = out.B_theta
    est = out.assume_dp_dF_correct()
    est.estimate_q(finesse_input)
    """
    B_fig = plt.figure("B")
    ax1 = plt.subplot2grid((2,2), (0,0), colspan=2)
    ax2 = plt.subplot2grid((2,2), (1,0))
    ax3 = plt.subplot2grid((2,2), (1,1))  
    ax2.set_aspect(1)
    ax3.set_aspect(1)
    
    

    
    ax1.plot(out.psi_finesse[0,:], np.abs(out.q_finesse[0,:]))
    ax1.set_xlabel("$\psi$")
    ax1.set_ylabel("$q$")    
    
    map2 = ax2.pcolormesh(out.x_map.points_x[:,:,0], out.x_map.points_x[:,:,1], np.abs(out.B_theta))    
    divider = make_axes_locatable(ax2)
    cax1 = divider.append_axes("right", "5%", pad="3%")
    cbar1 = plt.colorbar(map2, cax=cax1)
    cbar1.set_label(r"$\abs{B_p}[\si{T}]$")
    cax1.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=5))
    ax2.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=3))    
    ax2.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=5))
    ax2.set_xlabel("$R [\si{m}]$")
    ax2.set_ylabel("$Z [\si{m}]$") 
    
    map3 = ax3.pcolormesh(out.x_map.points_x[:,:,0], out.x_map.points_x[:,:,1], np.abs(out.B_phi))
    ax3.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=3))        
    ax3.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=5))
    divider = make_axes_locatable(ax3)
    cax2 = divider.append_axes("right", "5%", pad="3%")    
    cbar2 = plt.colorbar(map3, cax=cax2)
    cbar2.set_label(r"$\abs{B_\varphi}[\si{T}]$")
    cax2.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=5))
    ax3.set_ylabel("$Z [\si{m}]$")
    ax3.set_xlabel("$R [\si{m}]$")
    
    plt.tight_layout()
    B_fig.savefig(tex_path + 'B.pdf')
    """
    l = np.zeros([out.triangular_map.dl.shape[0] + 1, out.triangular_map.dl.shape[1]])
    for i in xrange(1, np.shape(out.triangular_map.dl)[0] + 1):
        for j in xrange(0, np.shape(out.triangular_map.dl)[1]):
            l[i,j] = l[i - 1, j] + out.triangular_map.dl[i - 1, j]
    B_theta_var_fig = plt.figure("B_theta_var")
    plt.plot(l[:,44]/l[-1,44], np.abs(out.B_p[:,44]), label=r"$\psi = 0.03$")
    plt.plot(l[:,99]/l[-1,99], np.abs(out.B_p[:,99]), label=r"$\psi = 0.15$")
    plt.plot(l[:,200]/l[-1,200], np.abs(out.B_p[:,200]), label=r"$\psi = 0.61$")
    plt.plot(l[:,256]/l[-1,250], np.abs(out.B_p[:,250]), label=r"$\psi = 0.95$")
    plt.xlim((0,1))
    plt.ylim((0,0.7))
    plt.legend(fontsize = "small") 
    plt.xlabel(r"$l/L$")
    plt.ylabel(r"$|B_p|$")
    B_theta_var_fig.savefig(tex_path + B_theta_var_fig.get_label() + '.pdf')
 
    
    #%% plot q
    
    q_fig = plt.figure("q_fig")
    plt.subplot(211)
    plt.plot(psi, abs(finesse_output.q_finesse[0,:]), label = "$FINESSE$")
    plt.plot(psi, abs(q_est), label = "$PF2q$")
    #plt.plot(psi, target.convert_rho_to_psi(psi, finesse_output.calculate_rho()), label = "$q_{target}$")
    plt.xlabel("$\psi$")
    plt.ylabel("$q$")
    plt.legend(loc = "upper left", fontsize = "small")
    
    plt.subplot(212)
    q_error = tools.relative_error(finesse_output.q_finesse[0,:], q_est)
    plt.plot(psi, q_error)
    #plt.plot(psi, target.convert_rho_to_psi(psi, finesse_output.calculate_rho()), label = "$q_{target}$")
    plt.xlabel(r"$\psi$")
    plt.ylabel(r"$\eta_q$")
    plt.tight_layout()
    q_fig.savefig(tex_path + q_fig.get_label() + '.pdf')
    
    karel_error = [0.0264777640992,
                   0.0100206084445,
                   0.0048280248912,
                   0.00343095068767,
                   0.00303307430314]
                   
    q_error_fig, (ax) = plt.subplots()
    plt.plot(npoints, karel_error)
    plt.xlabel("$\psi$")
    plt.ylabel(r"$\bar{\eta_q}$")
    
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(base=32))
    formatter = matplotlib.ticker.ScalarFormatter()
    formatter.set_powerlimits((-5,5))
    ax.xaxis.set_major_formatter(formatter)
    plt.xlim(xmax = 256+32)
    plt.xlabel(r"$N_R = N_t$")
    
    plt.tight_layout()
    q_error_fig.savefig(tex_path + 'q_error_fig.pdf')

    #%% plot grid stuff
    grid_fig = plt.figure("grid")
    ax = plt.subplot(111)
    plot_tools.plot_grid(ax, finesse_output.x_map)
    grid_fig.savefig(tex_path + 'grid.pdf')
    
    triangular_fig, axes = plt.subplots(1, 3)
    (ax1, ax2, ax3) = axes
    plot_tools.plot_grid(ax1, finesse_output.x_map)
    plot_tools.plot_grid(ax2, finesse_output.x_map)
    plot_tools.plot_grid(ax3, finesse_output.x_map)
    ax1.set_xlim([-0.01, 0.03])
    ax1.set_ylim([0.02, 0.07])
    ax3.set_xlim([0.3, 0.5])
    ax3.set_ylim([0.3, 0.6])
    rect1 = matplotlib.patches.Rectangle((-0.01, 0.02), 0.07 - 0.02, 0.03 -- 0.01, fill = False, zorder=1000)
    rect2 = matplotlib.patches.Rectangle((0.3, 0.3), 0.5 - 0.3, 0.6 -0.3, fill = False, zorder = 1000)
    
    ax2.add_patch(rect1)  
    ax2.add_patch(rect2)
    for ax in axes:
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)
    #triangular_fig = finesse_output.triangular_map.plot(figure_name = "triangular grid")["figure"]
    plt.tight_layout()    
    triangular_fig.savefig(tex_path + 'triangular_grid.pdf', bbox_inches='tight')
    

#    for results in pkl_results:
    def plot_derror(results, names):
        avg_error = 0.05
        q1_error = 0.02
        derror_P_fig, (ax_P_avg, ax_P_q1) = plt.subplots(2,1,num = names[0])
        
        plt.tight_layout()        
        derror_Q_fig, (ax_Q_avg, ax_Q_q1) = plt.subplots(2,1,num = names[1])
        plt.tight_layout()        
        ax_P_avg.set_xlim([-1, 1])
        #ax_P_avg.set_xlabel(r"$\Delta p$")
        ax_P_avg.set_ylabel(r"$\bar{\eta_q}$")
        ax_P_q1.set_xlim([-1, 1])
        ax_P_q1.set_xlabel(r"$\Delta p$")
        ax_P_q1.set_ylabel(r"$\eta_{q=1}$")
        ax_Q_avg.set_xlim([-30, 30])
        #ax_Q_avg.set_xlabel(r"$\Delta F^2$")
        ax_Q_avg.set_ylabel(r"$\bar{\eta_q}$")
        ax_Q_q1.set_xlim([-30, 30])
        ax_Q_q1.set_xlabel(r"$\Delta F^2$")
        ax_Q_q1.set_ylabel(r"$\eta_{q=1}$")
        #derror_P_fig = plt.figure("derror_p")
        #derror_Q_fig = plt.figure("derror_Q")
        for trial, values in results.iteritems():
            #init = getattr(result["initial_input"], result["poly"][0])[result["poly"][1]]
            #dresult = result["results"][:,0] - init
            if trial[0] == "Q_finesse_poly":
                name = r"$F^2_" + str(trial[1]) + r"$"
                ax_Q_avg.plot(values["results_avg"][:,0], values["results_avg"][:,1], label = name)
                ax_Q_avg.axhline(avg_error, linestyle="--", color = "c")
                ax_Q_avg.set_ylim([0, 2*avg_error])
                ax_Q_q1.plot(values["results_q1"][:,0], abs(values["results_q1"][:,1]), label = name)
                ax_Q_q1.axhline(q1_error, linestyle="--", color = "c")
                ax_Q_q1.set_ylim([0, 2*q1_error])  
                #ax_Q_q1.axhline(-0.02, linestyle="--", color = "c")
            elif trial[0] == "P_finesse_poly":
                name = r"$p_" + str(trial[1]) + r"$"
                ax_P_avg.plot(values["results_q1"][:,0]   , values["results_avg"][:,1], label = name)
                ax_P_avg.axhline(avg_error, linestyle="--", color = "c")              
                ax_P_avg.set_ylim([0, 2*avg_error])                
                ax_P_q1.plot(values["results_q1"][:,0], abs(values["results_q1"][:,1]), label = name)
                ax_P_q1.axhline(q1_error, linestyle="--", color = "c")
                ax_P_q1.set_ylim([0, 2*q1_error])  
                #ax_P_q1.axhline(-0.02, linestyle="--", color = "c")

        ax_P_avg.legend(fontsize = "small")
        ax_P_q1.legend(fontsize = "small")
        ax_Q_avg.legend(fontsize = "small")
        ax_Q_q1.legend(fontsize = "small")
        derror_P_fig.tight_layout()
        derror_Q_fig.tight_layout()
        derror_P_fig.savefig(tex_path + derror_P_fig.get_label() + '.pdf')
        derror_Q_fig.savefig(tex_path + derror_Q_fig.get_label() + '.pdf')
    
    pkl_file = open('bench_p33_Q12_P12.pkl', 'rb')  
    dpdF_result = pickle.load(pkl_file)
    pkl_file.close()
    pkl_file = open('bench_p33_Q345_P345.pkl', 'rb')
    dpdF_result.update(pickle.load(pkl_file))
    pkl_file.close()
    plot_derror(dpdF_result, ["delta_p", "delta_F2"])
    pkl_file = open('bench_p33_Q12_P12_const.pkl', 'rb')  
    dpdF_const_result = pickle.load(pkl_file)
    pkl_file.close()
    pkl_file = open('bench_p33_Q345_P345_const.pkl', 'rb')
    dpdF_const_result.update(pickle.load(pkl_file))
    pkl_file.close()
    #result[('Q_finesse_poly', 1)]["results_avg"] = result[('Q_finesse_poly', 1)]["results_avg"][:45,:]
    #result[('Q_finesse_poly', 1)]["results_q1"] = result[('Q_finesse_poly', 1)]["results_q1"][:45,:]    
   
    plot_derror(dpdF_const_result, ["delta_p_const", "delta_F2_const"])
    #fptool.FTool(session, finesse_input, target)
    
    
    #%% Surfaces change   
    
    def plot_shape(results):
        avg_error = 0.05
        q1_error = 0.02

        for trial_tuple, trial in results.iteritems():
            
            fig_tor = plt.figure("shape_tor", figsize=(10,3.8))
            ax1 = fig_tor.add_subplot(141)
            ax2 = fig_tor.add_subplot(142)
            ax3 = fig_tor.add_subplot(143)
            #fig_pol = plt.figure("shape_pol")
            ax4 = fig_tor.add_subplot(144)
            shape = trial['results_shape']
            for delta, shape in shape.iteritems():
                flux_surface = [1,17,32]
                colors = {-29.: 'b',
                          0.:'r',
                          29.:'g'}
                          
                xlim = {1:(0.02,0.14),
                        17:(-0.6,0.6),
                        32:(-1.2,1.2)}
#                ylim = {1:(-0.09,0.09),
#                        17:(1.5*-0.6,1.5*0.6),
#                        32:(-1.8,1.8)}
                ylim = {1:(-0.1,0.1),
                        17:(-1,1),
                        32:(-2,2)}
                if delta != -29. and delta !=0. and delta != 29.:
                    continue
                name = "$" + str(delta) + "$"
#                for i, ax in enumerate(fig.get_axes()):
                for i, ax in enumerate([ax1, ax2, ax3]):
                    line = ax.plot(shape[0][:,flux_surface[i]], 
                                shape[1][:,flux_surface[i]], 
                                label = name, color=colors[delta])
                    ax.set_xlim(xlim[flux_surface[i]])
                    ax.set_ylim(ylim[flux_surface[i]])
                    ax.set_title(r"$\psi \: = \:" + 
                                str(round(float(flux_surface[i])/shape[0].shape[1],1)) + "$")
                ax4.plot(np.transpose(shape[0][::4,:]), 
                         np.transpose(shape[1][::4,:]),color=colors[delta])
                ax4.set_xlim(xlim[flux_surface[i]])
                ax4.set_ylim(ylim[flux_surface[i]])
                ax4.set_title(r"$\vartheta$")
            #plt.legend(fontsize = "small")
            axes = fig_tor.get_axes()
            #axes.extend(fig_pol.get_axes())
            for ax in axes:
                ax.set_aspect(1)
#                ax.axes.get_xaxis().set_visible(False)
#                ax.axes.get_yaxis().set_visible(False)
#                ax.set_ylabel("$Z [\si{m}]$")
                ax.set_xlabel("$R [m]$")
#                ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins = 3))
#                ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins = 3))
                ax.xaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=3))
                ax.yaxis.set_major_locator(matplotlib.ticker.LinearLocator(numticks=3))
                formatter = matplotlib.ticker.ScalarFormatter()
                formatter.set_powerlimits((-3,3))
                formatter.set_scientific(False)
                ax.xaxis.set_major_formatter(formatter)
                ax.yaxis.set_major_formatter(formatter)
#                ax.set_ylim(ax3.get_ylim())
#                ax.set_xlim(ax3.get_xlim())
            ax1.set_ylabel("$Z [m]$")
            ax4.set_ylabel("$Z [m]$")
            fig_tor.tight_layout()   
            fig_tor.savefig(tex_path + fig_tor.get_label() + '.pdf')
        #derror_Q_fig.savefig(tex_path + derror_Q_fig.get_label() + '.pdf')
        
        
    pkl_file = open('shape.pkl', 'rb')
    shape_result = pickle.load(pkl_file)
    plot_shape(shape_result)
    

 
    
    plt.show()