#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains tools miscellaneous tools used throughout the PF2q module.
It also contains some deprecated functions that you can use at your own risk.
@author: Karel van de Plassche
@licence: GPLv3
"""

import os
import warnings
from math import ceil

import numpy as np
#from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

# Needed for file manipulation
from sys import platform
if platform == "win32":
    from win32com.client import Dispatch


def range_0_2pi(narray, tolerance=0.001):
    """Remap all values from [-2pi, 2pi] to [0, 2pi]."""
    # Prevent weird stuff around 000
    narray[abs(narray) < tolerance] = 0
    negative_indices = narray < 0
    narray[negative_indices] = narray[negative_indices] + 2 * np.pi
    return narray


def smart_diff(narray):
    """Calculate a smart diff.

    Calculate a smart diff over the poloidal axis (axis=0) exploiting that
    the first and last poloidal points of the FINESSE grid are the same point.
    """
    diff = np.diff(narray, axis=0)
    diff_list = np.empty(diff.shape[1])
    for j in xrange(diff.shape[1]):
        diff_list[j] = narray[0, j] - narray[-1, j]
    diff_simps = np.insert(diff, 0, diff_list, axis=0)
    return diff_simps


def rescale(values, new_0=1, new_1=0):
    """
    Linearly rescale an array of numbers.
    """
    scale = (new_0 - new_1) / (values[0] - values[-1])
    shift = new_0 - scale * values[0]
    if values.__class__ is np.lib.polynomial.poly1d:
        new_poly = np.poly1d(scale * values)
        new_poly[0] = values[0] + shift
        output = new_poly
    else:
        output = scale * values + shift

    return output, (scale, shift)

plotcounter = 0


def relative_error(real, estimate):
    return abs(1 - estimate / real)


def badness(rho_real, real, rho_est, est):
    """ Determine the badness of an estimate
    Calculate the relative errors at q = 1, q = 1.1, rho = .08, one-but-last
    element, and the average relative error. The value is negative if
    real < est.
    This is returned as the 'badness' together with the index of these points
    in the estimate array.

    Arguments:
    rho_real -- real values of rho
    real -- values of the function at the real values of rho
    rho_est -- estimated values of rho
    est -- values of the function at the estimated values of rho

    Returns:
    (total_badness,
                   ((badness_pre_q_1_index,  badness_pre_q_1),
                    (badness_q_1_index,      badness_q_1),
                    (badness_post_q_1_index, badness_post_q_1),
                    (badness_end_index,      badness_end),
                    (badness_max_index,      badness_max)))
    with:
    total_badness -- the average badness
    badness_* -- the badness at the specific point
    *_index -- the index of the point in rho_est
    """

    freal_vs_rho_real = extrap1d(interp1d(rho_real, real))
    # Remap real values
    real_resc = freal_vs_rho_real(rho_est)
    rel_error = relative_error(real_resc,
                               est)
    total_badness = np.nanmean(rel_error)

    # Find the index for which the real value is one
    index = np.int((np.abs(real_resc-1)).argmin())
    badness = rel_error[index]
    if real_resc[index] > est[index]:
        badness *= -1
    badness_q_1_index = index
    badness_q_1 = badness

    # Find the index for which the real rho is 0.08
    index = np.int((np.abs(rho_est-0.08)).argmin())
    badness = rel_error[index]
    if real_resc[index] > est[index]:
        badness *= -1
    badness_pre_q_1_index = index
    badness_pre_q_1 = badness

    # Find the index for which the real value is 1.1
    index = np.int((np.abs(real_resc-1.1)).argmin())
    badness = rel_error[index]
    if real_resc[index] > est[index]:
        badness *= -1
    badness_post_q_1_index = index
    badness_post_q_1 = badness

    # Find the one but last index
    index = -2
    badness = rel_error[index]
    if real_resc[index] > est[index]:
        badness *= -1
    badness_end_index = index
    badness_end = badness

    if len(np.where(np.nanmax(rel_error) == rel_error)[0]) != 0:
        badness_max_index = np.where(np.nanmax(rel_error) == rel_error)[0][0]
        badness_max = rel_error[badness_max_index]
    else:
        badness_max_index = 0
        badness_max = np.inf
    return (total_badness,
            ((badness_pre_q_1_index,  badness_pre_q_1),
             (badness_q_1_index,      badness_q_1),
             (badness_post_q_1_index, badness_post_q_1),
             (badness_end_index,      badness_end),
             (badness_max_index,      badness_max)))


def extrap1d(interpolator):
    xs = interpolator.x
    ys = interpolator.y

    def pointwise(x):
        if x < xs[0]:
            return ys[0]+(x-xs[0])*(ys[1]-ys[0])/(xs[1]-xs[0])
        elif x > xs[-1]:
            return ys[-1]+(x-xs[-1])*(ys[-1]-ys[-2])/(xs[-1]-xs[-2])
        else:
            return interpolator(x)

    def ufunclike(xs):
        return np.array(map(pointwise, np.array(xs)))

    return ufunclike


if platform == "win32":
    def create_windows_shortcut(src, dst):
        """
        Create a shortcut on a windows system. This function is deprecated.
        """
        warnings.warn("Function is deprecated and might give unexpected results")
        path = os.path.join(dst + ".lnk")
        target = src
        wDir = os.path.dirname(dst)
        icon = src
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Workingdirectory = wDir
        shortcut.IconLocation = icon
        shortcut.save()


def combine_badness((tot, ((i_0, bd0), (i_1, bd1),
                           (i_2, bd2), (i_3, bd3),
                           (i_4, bd4))), weights=[1, 4, 8, 6, 4]):
    """
    Combine the badness array generated with the badness() function into one
    combined badness number. Function is deprecated.
    """
    warnings.warn("Function is deprecated and might give unexpected results")
    badness = np.average([tot, bd0, bd1, bd2, bd3], weights=weights)
    if bd4 > 0.8:
        badness += bd4
    return badness


#def fit_finesse_poly(x, y):
#    """
#    Fit a polynomial with a constraint on the coefficients.
#    This function is deprecated.
#    """
#    warnings.warn("Function is deprecated and might give unexpected results")
#    constraint = 50
#    penalty = 1
#
#    def order3(x, p3, p2, p1, p0):
#        have_penalty = np.any(np.abs([p3, p2, p1, p0]) > constraint)
#        return p0 + p1 * x + p2 * x ** 2 + p3 * x ** 3 + have_penalty * penalty
#
#    def order4(x, p4, p3, p2, p1, p0):
#        have_penalty = np.any(np.abs([p4, p3, p2, p1, p0]) > constraint)
#        return p0 + p1 * x + p2 * x ** 2 + p3 * x ** 3 + p4 * x ** 4 + have_penalty * penalty
#
#    def order5(x, p5, p4, p3, p2, p1, p0):
#        have_penalty = np.any(np.abs([p5, p4, p3, p2, p1, p0]) > constraint)
#        return p0 + p1 * x + p2 * x ** 2 + p3 * x ** 3 + p4 * x ** 4 + p5 * x ** 5 + have_penalty * penalty
#
#    def order6(x, p6, p5, p4, p3, p2, p1, p0):
#        have_penalty = np.any(np.abs([p6, p5, p4, p3, p2, p1, p0]) > constraint)
#        return p0 + p1 * x + p2 * x ** 2 + p3 * x ** 3 + p4 * x ** 4 + p5 * x ** 5 + p6 * x ** 6 + have_penalty * penalty
#
#    def order7(x, p7, p6, p5, p4, p3, p2, p1, p0):
#        have_penalty = np.any(np.abs([p7, p6, p5, p4, p3, p2, p1, p0]) > constraint)
#        return p0 + p1 * x + p2 * x ** 2 + p3 * x ** 3 + p4 * x ** 4 + p5 * x ** 5 + p6 * x ** 6 + p7 * x ** 7 + have_penalty * penalty
#    poly_list = [order3, order4, order5, order6, order7]
#
#    polies = []
#    for i, poly in enumerate(poly_list):
#        if i == 0:
#            init_guess = [1, 1, 1, 1]
#        else:
#            init_guess = np.append(polies[i-1], 1)
#
#        popt, pcov, infodict, errmsg, ier = curve_fit(poly, x, y,
#                                                      p0=init_guess,
#                                                      full_output=True)
#        polies.append(popt)
#        values = np.polyval(popt, x)
#        values_mean = np.mean(values)
#        ss_tot = np.sum((values - values_mean) ** 2)
#        ss_res = np.sum((values - y) ** 2)
#        rsquared = 1-(ss_res / ss_tot)
#
#        bestFit = popt
#
#    return bestFit


def frange(start, stop=None, step=1, precision=3):
    """frange generates a set of floating point values over the
    This function is deprecated.
    range [start, stop] with step size step rounded with precision places
    after the decimal point.

    frange([start,] stop [, step ])
    """
    warnings.warn("Function is deprecated and might give unexpected results")
    _xrange = xrange
    if stop is None:
        for x in _xrange(int(ceil(start))):
            yield x
    else:
        # create a generator expression for the index values
        indices = (i for i in _xrange(0, int(round((stop-start)/step + 1,
                                                   precision))))
        # yield results
        for i in indices:
            yield start + step*i
