# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Scientific Package. This package holds all simulators, and
# analysers necessary to run brain-simulations. You can use it stand alone or
# in conjunction with TheVirtualBrain-Framework Package. See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
# CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Test history in simulator.

.. moduleauthor:: Marmaduke Woodman <mw@eml.cc>

"""

if __name__ == "__main__":
    from tvb.tests.library import setup_test_console_env
    setup_test_console_env()

import numpy
import unittest
import tvb.basic.traits.types_basic as basic
from tvb.datatypes.connectivity import Connectivity
from tvb.simulator.coupling import Coupling
from tvb.simulator.integrators import Identity
from tvb.simulator.models import Model
from tvb.simulator.monitors import Raw
from tvb.simulator.simulator import Simulator
from tvb.tests.library.base_testcase import BaseTestCase



class IdCoupling(Coupling):
    """Implements an identity coupling function."""

    def __call__(self, step, history):
        g_ij = history.es_weights
        x_i, x_j = history.query(step)
        return (g_ij * x_j).sum(axis=2).transpose((1, 0, 2))



class Sum(Model):
    nvar = 1
    _nvar = 1
    state_variable_range = {'x': [0, 100]}
    variables_of_interest = basic.Enumerate(default=['x'], options=['x'])
    state_variables = ['x']
    cvar = numpy.array([0])

    def dfun(self, X, coupling, local_coupling=0):
        return X + coupling + local_coupling



class ExactPropagationTests(BaseTestCase):

    def build_simulator(self, n=4):

        self.conn = numpy.zeros((n, n), numpy.int32)
        for i in range(self.conn.shape[0] - 1):
            self.conn[i, i + 1] = 1

        self.dist = numpy.r_[:n * n].reshape((n, n))
        self.sim = Simulator(
            conduction_speed=1,
            coupling=IdCoupling(),
            surface=None,
            stimulus=None,
            integrator=Identity(dt=1),
            initial_conditions=numpy.ones((n * n, 1, n, 1)),
            simulation_length=10,
            connectivity=Connectivity(weights=self.conn, tract_lengths=self.dist, speed=1),
            model=Sum(),
            monitors=(Raw(), ),
        )
        self.sim.configure()


    def test_propagation(self):
        n = 4
        self.build_simulator(n=n)
        # x = numpy.zeros((n, ))
        xs = []
        for (t, raw), in self.sim(simulation_length=10):
            xs.append(raw.flat[:].copy())
        xs = numpy.array(xs)
        xs_ = numpy.array([[2., 2., 2., 1.],
                           [3., 3., 3., 1.],
                           [5., 4., 4., 1.],
                           [8., 5., 5., 1.],
                           [12., 6., 6., 1.],
                           [17., 7., 7., 1.],
                           [23., 8., 8., 1.],
                           [30., 10., 9., 1.],
                           [38., 13., 10., 1.],
                           [48., 17., 11., 1.]])
        self.assertTrue(numpy.allclose(xs, xs_))



def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(ExactPropagationTests))
    return test_suite



if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE)
