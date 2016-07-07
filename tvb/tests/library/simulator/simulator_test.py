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

Tests all the possible combinations of (available) models and integration 
schemes (region and surface based simulations).

.. moduleauthor:: Paula Sanz Leon <sanzleon.paula@gmail.com@>
.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>

"""

#TODO: check the defaults of simulator.Simulator() (?)
#TODO: continuation support or maybe test that particular feature elsewhere

if True or __name__ == "__main__":
    from tvb.tests.library import setup_test_console_env
    setup_test_console_env()

import os
import numpy
import unittest
import itertools
from tvb.simulator.common import get_logger
from tvb.simulator import simulator, models, coupling, integrators, monitors, noise
from tvb.datatypes import connectivity, sensors
from tvb.datatypes.cortex import Cortex
from tvb.datatypes.local_connectivity import LocalConnectivity
from tvb.datatypes.region_mapping import RegionMapping
from tvb.basic.traits.parameters_factory import get_traited_subclasses
from tvb.tests.library.base_testcase import BaseTestCase

LOG = get_logger(__name__)

sens_meg = sensors.SensorsMEG(load_default=True)
sens_eeg = sensors.SensorsEEG(load_default=True)
AVAILABLE_MODELS = get_traited_subclasses(models.Model)
AVAILABLE_METHODS = get_traited_subclasses(integrators.Integrator)
MODEL_CLASSES = AVAILABLE_MODELS.values()
METHOD_NAMES = AVAILABLE_METHODS.keys()
METHOD_NAMES.append('RungeKutta4thOrderDeterministic')


class Simulator(object):
    """
    Simulator test class
    
    """
    def __init__(self): 
        """
        Initialise the structural information, coupling function, and monitors.
        
        """

        #Initialise some Monitors with period in physical time
        raw     = monitors.Raw()
        gavg    = monitors.GlobalAverage(period=2 ** -2)
        subsamp = monitors.SubSample(period=2 ** -2)
        tavg    = monitors.TemporalAverage(period=2 ** -2)
        #spheeg  = monitors.SphericalEEG(sensors=sens_eeg, period=2 ** -2)
        #sphmeg  = monitors.SphericalMEG(sensors=sens_meg, period=2 ** -2)
        # TODO test all monitors
        
        self.monitors = (raw, gavg, subsamp, tavg) 

        self.method = None
        self.sim    = None


    def run_simulation(self, simulation_length=2 ** 2):
        """
        Test a simulator constructed with one of the <model>_<scheme> methods.
        """

        raw_data, gavg_data, subsamp_data, tavg_data = [], [], [], []
        # spheeg_data, sphmeg_data = [], []

        for raw, gavg, subsamp, tavg in self.sim(simulation_length=simulation_length):    

            if not raw is None:
                raw_data.append(raw)

            if not gavg is None:
                gavg_data.append(gavg)

            if not subsamp is None:
                subsamp_data.append(subsamp)

            if not tavg is None:
                tavg_data.append(tavg)
                
            # if not spheeg is None:
            #     spheeg_data.append(spheeg)
                
            # if not sphmeg is None:
            #     sphmeg_data.append(sphmeg)
                

    def configure(self, dt=2 ** -3, model=models.Generic2dOscillator, speed=4.0,
                  coupling_strength=0.00042, method="HeunDeterministic", 
                  surface_sim=False,
                  default_connectivity=True):
        """
        Create an instance of the Simulator class, by default use the
        generic plane oscillator local dynamic model and the deterministic 
        version of Heun's method for the numerical integration.
        
        """
        self.method = method
        
        if default_connectivity:
            white_matter = connectivity.Connectivity(load_default=True)
            region_mapping = RegionMapping.from_file(source_file="regionMapping_16k_76.txt")
        else:
            white_matter = connectivity.Connectivity.from_file(source_file="connectivity_192.zip")
            region_mapping = RegionMapping.from_file(source_file="regionMapping_16k_192.txt")


        white_matter_coupling = coupling.Linear(a=coupling_strength)    
        white_matter.speed = speed

        dynamics = model()
        
        if method[-10:] == "Stochastic":
            hisss = noise.Additive(nsig=numpy.array([2 ** -11]))
            integrator = eval("integrators." + method + "(dt=dt, noise=hisss)")
        else:
            integrator = eval("integrators." + method + "(dt=dt)")
        
        if surface_sim:
            local_coupling_strength = numpy.array([2 ** -10])
            default_cortex = Cortex(load_default=True, region_mapping_data=region_mapping)
            default_cortex.coupling_strength = local_coupling_strength
            default_cortex.local_connectivity = LocalConnectivity(load_default=default_connectivity,
                                                                           surface=default_cortex)
        else: 
            default_cortex = None

        # Order of monitors determines order of returned values.
        self.sim = simulator.Simulator(model=dynamics,
                                       connectivity=white_matter,
                                       coupling=white_matter_coupling,
                                       integrator=integrator,
                                       monitors=self.monitors,
                                       surface=default_cortex)
        self.sim.configure()
        


class SimulatorTest(BaseTestCase):

    def test_simulator_region(self):
        #init
        test_simulator = Simulator()
    
        #test cases
        for model_class, method_name in itertools.product(MODEL_CLASSES, METHOD_NAMES):
            test_simulator.configure(model=model_class,
                                     method=method_name,
                                     surface_sim=False)
            test_simulator.run_simulation()
            
            
    def test_simulator_surface(self): 
        """
        This test mainly evaluates if surface simulations run when
        subcortical structures are included. 
       
        TODO: 
            Should be as complete as the one for region simulations.

        """
        test_simulator = Simulator()

        for default_connectivity in [True, False]:
            test_simulator.configure(surface_sim=True, default_connectivity=default_connectivity)
            test_simulator.run_simulation(simulation_length=2)
            LOG.debug("Surface simulation finished for defaultConnectivity= %s" % str(default_connectivity))



def suite():
    """
    Gather all the tests in a test suite.
    """
    test_suite = unittest.TestSuite()
    test_suite.addTest(unittest.makeSuite(SimulatorTest))
    return test_suite


if __name__ == "__main__":
    #So you can run tests from this package individually.
    TEST_RUNNER = unittest.TextTestRunner()
    TEST_SUITE = suite()
    TEST_RUNNER.run(TEST_SUITE) 
