# -*- coding: utf-8 -*-
#
#
#  TheVirtualBrain-Scientific Package. This package holds all simulators, and
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
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
Test for tvb.simulator.coupling module

.. moduleauthor:: Paula Sanz Leon <sanzleon.paula@gmail.com>

"""

if True or __name__ == "__main__":
    from tvb.tests.library import setup_test_console_env
    setup_test_console_env()

import copy
import numpy
import unittest
from tvb.tests.library.base_testcase import BaseTestCase
from tvb.simulator import coupling, models, simulator
from tvb.datatypes import cortex, connectivity
from tvb.simulator.history import SparseHistory

class CouplingTest(BaseTestCase):
    """
    Define test cases for coupling:
        - initialise each class
        - check functionality
        
    """
    weights = numpy.array([[0, 1], [1, 0]])
    weights = weights[:, numpy.newaxis, :, numpy.newaxis]  # nodes, ncvar, nodes, modes

    state_1sv = numpy.array([[[1], [2]]])               # (state_variables, nodes, modes)
    state_2sv = numpy.array([[[1], [2]], [[1], [2]]])
    delayed_state_1sv = numpy.ones((2, 1, 2, 1))        # nodes, state_variables, nodes, modes
    delayed_state_2sv = numpy.ones((2, 2, 2, 1))

    weights2d = weights[:, 0, :, 0]
    history_1sv = SparseHistory(weights2d, weights2d*0, numpy.r_[0], 1)
    history_2sv = SparseHistory(weights2d, weights2d*0, numpy.r_[0, 1], 1)


    def _apply_coupling(self, k):
        k.configure()
        k(0, self.history_1sv)


    def _apply_coupling_2sv(self, k):
        k.configure()
        k(0, self.history_2sv)


    def test_difference_coupling(self):
        k = coupling.Difference()
        self.assertEqual(k.a, 0.1)
        self._apply_coupling(k)


    def test_hyperbolic_coupling(self):
        k = coupling.HyperbolicTangent()
        self.assertEqual(k.a, 1)
        self.assertEqual(k.b, 1)
        self.assertEqual(k.midpoint, 0)
        self.assertEqual(k.sigma, 1)
        self._apply_coupling(k)


    def test_kuramoto_coupling(self):
        k = coupling.Kuramoto()
        self.assertEqual(k.a, 1)
        self._apply_coupling(k)


    def test_linear_coupling(self):
        k = coupling.Linear()
        self.assertEqual(k.a, 0.00390625)
        self.assertEqual(k.b, 0.0)
        self._apply_coupling(k)


    def test_pre_sigmoidal_coupling(self):
        k = coupling.PreSigmoidal()
        self.assertEqual(k.H, 0.5)
        self.assertEqual(k.Q, 1.)
        self.assertEqual(k.G, 60.)
        self.assertEqual(k.P, 1.)
        self.assertEqual(k.theta, 0.5)
        self.assertEqual(k.dynamic, True)
        self.assertEqual(k.globalT, False)
        self._apply_coupling_2sv(k)


    def test_scaling_coupling(self):
        k = coupling.Scaling()
        # Check scaling -factor
        self.assertEqual(k.a, 0.00390625)
        self._apply_coupling(k)


    def test_sigmoidal_coupling(self):
        k = coupling.Sigmoidal()
        self.assertEqual(k.cmin, -1.0)
        self.assertEqual(k.cmax, 1.0)
        self.assertEqual(k.midpoint, 0.0)
        self.assertEqual(k.sigma, 230.)
        self.assertEqual(k.a, 1.0)
        self._apply_coupling(k)


    def test_sigmoidal_jr_coupling(self):
        k = coupling.SigmoidalJansenRit()
        self.assertEqual(k.cmin, 0.0)
        self.assertEqual(k.cmax, 2.0 * 0.0025)
        self.assertEqual(k.midpoint, 6.0)
        self.assertEqual(k.r, 1.0)
        self.assertEqual(k.a, 0.56)
        self._apply_coupling_2sv(k)


class CouplingShapeTest(BaseTestCase):

    def test_shape(self):

        # try to avoid introspector picking up this model
        Gen2D = copy.deepcopy(models.Generic2dOscillator)

        class CouplingShapeTestModel(Gen2D):
            def __init__(self, test_case=None, n_node=None, **kwds):
                super(CouplingShapeTestModel, self).__init__(**kwds)
                self.cvar = numpy.r_[0, 1]
                self.n_node = n_node
                self.test_case = test_case

            def dfun(self, state, coupling, local_coupling):
                if self.test_case is not None:
                    self.test_case.assertEqual(
                        (2, self.n_node, 1),
                        coupling.shape
                    )
                    return state

        surf = cortex.Cortex(load_default=True)
        sim = simulator.Simulator(
            model=CouplingShapeTestModel(self, surf.vertices.shape[0]),
            connectivity=connectivity.Connectivity(load_default=True),
            surface=surf)

        sim.configure()

        for _ in sim(simulation_length=sim.integrator.dt * 2):
            pass

def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(CouplingTest))
    test_suite.addTest(unittest.makeSuite(CouplingShapeTest))
    return test_suite



if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE) 