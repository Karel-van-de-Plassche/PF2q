#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module contains tools to to work with the FINESSE grid, as well as
functions to do spatial integrals.
@author: Karel van de Plassche
@licence: GPLv3
"""
import numpy as np
import pf2q.tools as tools


def surfaceTriangle(A, B, C):
    """Calculate the surface of a triangle of which the vertices are known.
    By convention [:,:,1] means y, [:,:,0] means x.
    Calculate the surface using abs(Ax(By - Cy) + Bx(Cy - Ay) + Cx(Ay - By))/2
    (http://www.mathopenref.com/coordtrianglearea.html)
    """
    return abs(A[:, :, 0] * (B[:, :, 1] - C[:, :, 1]) +
               B[:, :, 0] * (C[:, :, 1] - A[:, :, 1]) +
               C[:, :, 0] * (A[:, :, 1] - B[:, :, 1]))/2


class Map(object):
    def __init__(self, x_grid, y_grid, O=(0, 0)):
        self.points_x = np.dstack((x_grid, y_grid))
        self.O = O
        self.points_x_O = None
        self.points_r = None
        self.points_r_O = None
        self.dl = None

    def calculate_poloidal(self):
        """Transpose (x,y) -> (r,chi)

        By convention: [:,:,0] = x,r and [:,:,1] = y,chi
        """
        if self.points_x_O is None:
            self.points_x_O = np.empty_like(self.points_x)
            self.points_x_O[:, :, 0] = self.points_x[:, :, 0] - self.O[0]
            self.points_x_O[:, :, 1] = self.points_x[:, :, 1] - self.O[1]
        if self.points_r_O is None:
            self.points_r_O = np.empty_like(self.points_x)
            self.points_r_O = np.dstack((np.squeeze(np.sqrt(
                                    self.points_x_O[:, :, 0] ** 2 +
                                    self.points_x_O[:, :, 1] ** 2)),
                                                   np.arctan2(
                                    self.points_x_O[:, :, 1],
                                    self.points_x_O[:, :, 0])))
            self.points_r_O[-1, :, 1].fill(2*np.pi)
            tools.range_0_2pi(self.points_r_O[:, :, 1])

    def calculate_dl(self):
        """Calulate dl along a flux surface

        This function estimates differentials using linear interpolation.
        So: dx[i] = x[i] - x[i - 1]
        """
        if self.points_r_O is None:
            self.calculate_poloidal()
        r_MA_inter = (self.points_r_O[:-1, :, 0] +
                      np.diff(self.points_r_O[:, :, 0], axis=0) / 2)
        chi_MA_inter = (self.points_r_O[:-1, :, 1] +
                        np.diff(self.points_r_O[:, :, 1], axis=0) / 2)

        x_MA_inter = r_MA_inter * np.cos(chi_MA_inter)
        y_MA_inter = r_MA_inter * np.sin(chi_MA_inter)
        if self.dl is None:
            self.dl = np.sqrt(tools.smart_diff(x_MA_inter) ** 2 +
                              tools.smart_diff(y_MA_inter) ** 2)
        return self.dl

    def contour_integral(self, value):
        """Calculate the integral along a flux surface"""
        dl = self.calculate_dl()
        result = sum(value * dl, 0)
        return result, dl

    def triangulate(self):
        """Convert the map to a triangular map"""
        return TriangularMap(self.points_x[:, :, 0],
                             self.points_x[:, :, 1],
                             O=self.O)


class QuadrilateralMap(Map):
    """Map of the FEM Quadrilateral
    Each quadrilateral is uniquely defined by its lowest corner, called A. The
    coordinates of the first element is A(x(P=0, R=0), y(P=0, R=0)) with P the
    poloidal coordinate and R the radial coordinate. Next elements are
    defined by continuing P counterclockwise and R inward to outward. Point
    B,C and D are the counterclockwise next corners.
    """
    vertices = ['A', 'B', 'C', 'D']

    def __init__(self, x_grid, y_grid, O=(0, 0)):
        super(QuadrilateralMap, self).__init__(x_grid, y_grid, O=O)
        self.A, self.B, self.C, self.D = self.abcdize(self.points_x)
        self.O = O

    def abcdize(self, grid):
        """
        Creates a grid of quatrilaterals ABCD. This is not really quick,
        but makes calculations more intuative.
        """
        A = grid[:-1, :-1]
        B = grid[1:, :-1]
        C = grid[1:, 1:]
        D = grid[:-1, 1:]
        return A, B, C, D


class TriangularMap(QuadrilateralMap):
    """Map of the FEM Triangular
    Each point is uniquely defined by the lowest corner of the quadrilateral,
    called A. Each triangle has a centroid: the arithmetic mean position of
    all the points in the shape. These are called G for triangle ABD and H
    for BCD.
    """
    triangle_1_vertices = ['A', 'B', 'D']
    triangle_2_vertices = ['B', 'C', 'D']

    def __init__(self, x_grid, y_grid, O=(0, 0)):
        super(TriangularMap, self).__init__(x_grid, y_grid, O=O)
        self.G = None
        self.H = None
        self.T = None
        self.U = None
        self.RG = None
        self.RH = None
        self.SABD = None
        self.SBCD = None

    def volume_integral(self, value, R0):
        """
        Calculates the volume integral of an infinitesimal toroidal ring
        iiint(value * dV)
        """
        self.calculate_centroid()
        self.RG = R0 + self.G[:, :, 0]
        self.RH = R0 + self.H[:, :, 0]
        ((dsurface_1, dvalue_1),
         (dsurface_2, dvalue_2), __) = self.centroid_interpolation(value)
        dvolume_1 = dsurface_1 * 2 * np.pi * self.RG
        dvolume_2 = dsurface_2 * 2 * np.pi * self.RH
        volume = np.sum(dvolume_1) + np.sum(dvolume_2)
        result = np.sum(dvolume_1 * dvalue_1) + np.sum(dvolume_2 * dvalue_2)

        return (result, volume), ((dvalue_1, dvolume_1), (dvalue_2, dvolume_2))

    def ring_integral(self, value):
        """
        Calculates the surface integral of an infinitesimal ring
        iint_0^x(value * dA)

        Arguments:
        value -- the value being integrated

        Returns:
        value_encl -- the result of iint_0^x(value * dA) where x is the index
        """
        (__, __), ((dvalue_1, dsurface_1),
                   (dvalue_2, dsurface_2)) = self.surface_integral(value)
        dvalue_encl_ring = np.sum(dvalue_1 * dsurface_1 +
                                  dvalue_2 * dsurface_2, axis=0)
        value_encl = np.empty_like(dvalue_encl_ring)
        for i in xrange(1, len(dvalue_encl_ring) + 1):
            value_encl[i - 1] = sum(dvalue_encl_ring[0:i])
        return value_encl

    def surface_integral(self, value):
        """ Calculate the surface intergral on a triangular map
        Calculate the surface integral using a FEM method.

        Arguments:
        value -- the value being integrated

        Returns:
        (result, surface), ((dvalue_1, dsurface_1),
                            (dvalue_2, dsurface_2))
        in which the dsurface is the surface of one triangle and dvalue is
        the estimated value on that triangle

        """
        ((dsurface_1, dvalue_1),
         (dsurface_2, dvalue_2), __) = self.centroid_interpolation(value)

        surface = np.sum(dsurface_1) + np.sum(dsurface_2)
        result = np.sum(dsurface_1 * dvalue_1) + np.sum(dsurface_2 * dvalue_2)
        return (result, surface), ((dvalue_1, dsurface_1),
                                   (dvalue_2, dsurface_2))

    def calculate_centroid(self):
        """
        Calculate the position of centroid G on triange ABD and centroid H on
        triangle BCD
        """
        if self.G is None or self.H is None:
            self.G = (self.A + self.B + self.D)/3
            self.H = (self.C + self.B + self.D)/3

    def centroid_interpolation(self, value_grid):
        Av, Bv, Cv, Dv = self.abcdize(np.tile(np.atleast_3d(value_grid),
                                              (1, 1, 2)))
        if self.G is None or self.H is None:
            # Create triangles with G as centroid of triangle_1 and H as
            # centroid of triangle_2
            self.calculate_centroid()

        if self.SABD is None or self.SBCD is None:
            self.SABD = surfaceTriangle(self.A, self.B, self.D)
            self.SBCD = surfaceTriangle(self.B, self.C, self.D)

        # The value at G and H is also just the geometric average
        value_triangle_1 = (Dv[:, :, 0] + Bv[:, :, 0] + Av[:, :, 0])/3
        value_triangle_2 = (Dv[:, :, 0] + Cv[:, :, 0] + Bv[:, :, 0])/3

        return ((self.SABD, value_triangle_1), (self.SBCD, value_triangle_2),
                (self.G, self.H))

    def barycentric_interpolation(self, value_grid):
        # Create triangles with T as barycenter of triangle_1 and U as
        # barycenter of triangle_2
        triangles = np.array([['A', 'B', 'T'],
                              ['D', 'A', 'T'],
                              ['B', 'D', 'T'],
                              ['B', 'C', 'U'],
                              ['D', 'B', 'U'],
                              ['C', 'D', 'U']])
        # Calculate the value at the gridpoints
        Av, Bv, Cv, Dv = self.abcdize(np.tile(np.atleast_3d(value_grid),
                                              (1, 1, 2)))
        Tv = Av + Bv + Dv
        self.T = (Av/Tv * self.A +
                  Bv/Tv * self.B +
                  Dv/Tv * self.D)

        Uv = Cv + Bv + Dv
        self.U = (Cv/Uv * self.C +
                  Bv/Uv * self.B +
                  Dv/Uv * self.D)

        # Use the surfaces of the triangles to calculate lambda
        lambda_ = np.empty(np.append(self.A.shape[0:2], 6), dtype='f')
        surface = np.dstack((surfaceTriangle(self.A, self.B, self.D),
                             surfaceTriangle(self.B, self.C, self.D)))

        for i, triangle in enumerate(triangles):
            surface = surfaceTriangle(getattr(self, triangle[0]),
                                      getattr(self, triangle[1]),
                                      getattr(self, triangle[2]))
            if triangle[2] == "T":
                total_triangle = 0
            else:
                total_triangle = 1
            lambda_[:, :, i] = surface / surface[:, :, total_triangle]
            if np.all(surface[:, 0, total_triangle] == 0):
                lambda_[:, 0, i] = np.full_like(lambda_[:, 0, i], 1/3)

        value_triangle_1 = (lambda_[:, :, 0] * Dv[:, :, 0] +
                            lambda_[:, :, 1] * Bv[:, :, 0] +
                            lambda_[:, :, 2] * Av[:, :, 0])
        value_triangle_2 = (lambda_[:, :, 3] * Dv[:, :, 0] +
                            lambda_[:, :, 4] * Cv[:, :, 0] +
                            lambda_[:, :, 5] * Bv[:, :, 0])

        # U and T are value dependent, so no need to save it
        self.U = None
        self.T = None
        return ((np.squeeze(surface[:, :, 0]), value_triangle_1),
                (np.squeeze(surface[:, :, 1]), value_triangle_2))
