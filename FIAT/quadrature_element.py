# -*- coding: utf-8 -*-

# Copyright (C) 2007-2016 Kristian B. Oelgaard
#
# This file is part of FFC.
#
# FFC is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# FFC is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with FFC. If not, see <http://www.gnu.org/licenses/>.
#
# Modified by Garth N. Wells 2006-2009

# Python modules.
import numpy

# FFC modules.
from ffc.log import error, info_red

# FIAT modules.
from FIAT.functional import PointEvaluation


class QuadratureElement:

    """Write description of QuadratureElement"""

    def __init__(self, ref_el, points):
        "Create QuadratureElement"

        # Save the quadrature points
        self._points = points

        # Create entity dofs.
        self._entity_dofs = _create_entity_dofs(ref_el, len(points))

        # The dual is a simply the PointEvaluation at the quadrature points
        # FIXME: KBO: Check if this gives expected results for code like evaluate_dof.
        self._dual = [PointEvaluation(ref_el, tuple(point)) for point in points]

    def space_dimension(self):
        "The element space dimension is simply the number of quadrature points"
        return len(self._points)

    def value_shape(self):
        "The QuadratureElement is scalar valued"
        return ()

    def entity_dofs(self):
        "Entity dofs are like that of DG, all internal to the cell"
        return self._entity_dofs

    def mapping(self):
        "The mapping is not really affine, but it is easier to handle the code generation this way."
        return ["affine"] * self.space_dimension()

    def dual_basis(self):
        "Return list of PointEvaluations"
        return self._dual

    def tabulate(self, order, points):
        """Return the identity matrix of size (num_quad_points, num_quad_points),
        in a format that monomialintegration and monomialtabulation understands."""

        # Derivatives are not defined on a QuadratureElement
        # FIXME: currently this check results in a warning (should be RuntimeError)
        # because otherwise some forms fails if QuadratureElement is used in a
        # mixed element e.g.,
        # element = CG + QuadratureElement
        # (v, w) = BasisFunctions(element)
        # grad(w): this is in error and should result in a runtime error
        # grad(v): this should be OK, but currently will raise a warning because
        # derivatives are tabulated for ALL elements in the mixed element.
        # This issue should be fixed in UFL and then we can switch on the
        # RuntimeError again.
        if order:
            # error("Derivatives are not defined on a QuadratureElement")
            info_red("\n*** WARNING: Derivatives are not defined on a QuadratureElement,")
            info_red("             returning values of basisfunction.\n")

        # Check that incoming points are equal to the quadrature points.
        if len(points) != len(self._points) or abs(numpy.array(points) - self._points).max() > 1e-12:
            print("\npoints:\n", numpy.array(points))
            print("\nquad points:\n", self._points)
            error("Points must be equal to coordinates of quadrature points")

        # Return the identity matrix of size len(self._points) in a
        # suitable format for tensor and quadrature representations.
        values = numpy.eye(len(self._points))
        return {(0,) * self._geometric_dimension: values}


def _create_entity_dofs(fiat_cell, num_dofs):
    "This function is ripped from FIAT/discontinuous_lagrange.py"
    entity_dofs = {}
    top = fiat_cell.get_topology()
    for dim in sorted(top):
        entity_dofs[dim] = {}
        for entity in sorted(top[dim]):
            entity_dofs[dim][entity] = []
    entity_dofs[dim][0] = list(range(num_dofs))
    return entity_dofs
