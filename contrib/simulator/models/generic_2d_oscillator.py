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
A abstract 2d oscillator model.

.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>

"""

# Third party python libraries
import numpy

#The Virtual Brain
from tvb.simulator.common import psutil, get_logger
LOG = get_logger(__name__)

import tvb.datatypes.arrays as arrays
import tvb.basic.traits.types_basic as basic 
import tvb.simulator.models as models



class Generic2dOscillator(models.Model):
    """
    The Generic2dOscillator model is ...
    
    .. [FH_1961] FitzHugh, R., *Impulses and physiological states in theoretical
        models of nerve membrane*, Biophysical Journal 1: 445, 1961. 
    
    .. [Nagumo_1962] Nagumo et.al, *An Active Pulse Transmission Line Simulating
        Nerve Axon*, Proceedings of the IRE 50: 2061, 1962.
    
    See also, http://www.scholarpedia.org/article/FitzHugh-Nagumo_model
    
    The models (:math:`V`, :math:`W`) phase-plane, including a representation of
    the vector field as well as its nullclines, using default parameters, can be
    seen below:
        
        .. _phase-plane-FHN:
        .. figure :: img/Generic2dOscillator_01_mode_0_pplane.svg
            :alt: Fitzhugh-Nagumo phase plane (V, W)
            
            The (:math:`V`, :math:`W`) phase-plane for the Fitzhugh-Nagumo 
            model.
            
    .. #Currently there seems to be a clash betwen traits and autodoc, autodoc
    .. #can't find the methods of the class, the class specific names below get
    .. #us around this...
    .. automethod:: Generic2dOscillator.__init__
    .. automethod:: Generic2dOscillator.dfun
    
    """
    
    _ui_name = "Generic 2d Oscillator"
    ui_configurable_parameters = ['tau', 'a', 'b', 'omega', 'upsilon', 'gamma', 'eta']
    #Define traited attributes for this model, these represent possible kwargs.
    tau = arrays.FloatArray(
        label = ":math:`\\tau`",
        default = numpy.array([1.25]),
        range = Range(lo = 0.01, hi = 5.0, step = 0.01),
        doc = """A time-scale separation between the fast, :math:`V`, and slow,
            :math:`W`, state-variables of the model.""")
    
    a = arrays.FloatArray(
        label = ":math:`a`",
        default = numpy.array([1.05]),
        range = basic.Range(lo = -1.0, hi = 1.5, step = 0.01),
        doc = """ratio a/b gives W-nullcline slope""")
    
    b = arrays.FloatArray(
        label = ":math:`b`",
        default = numpy.array([0.2]),
        range = basic.Range(lo = 0.0, hi = 1.0, step = 0.01),
        doc = """dimensionless parameter""")
    
    omega = arrays.FloatArray(
        label = ":math:`\\omega`",
        default = numpy.array([1.0]),
        range = basic.Range(lo = 0.0, hi = 1.0, step = 0.01),
        doc = """dimensionless parameter""")
    
    upsilon = arrays.FloatArray(
        label = ":math:`\\upsilon`",
        default = numpy.array([1.0]),
        range = basic.Range(lo = 0.0, hi = 1.0, step = 0.01),
        doc = """dimensionless parameter""")
    
    gamma = arrays.FloatArray(
        label = ":math:`\\gamma`",
        default = numpy.array([1.0]),
        range = basic.Range(lo = 0.0, hi = 1.0, step = 0.01),
        doc = """dimensionless parameter""")
    
    eta = arrays.FloatArray(
        label = ":math:`\\eta`",
        default = numpy.array([1.0]),
        range = basic.Range(lo = 0.0, hi = 1.0, step = 0.01),
        doc = """ratio :math:`\\eta/b` gives W-nullcline intersect(V=0)""")
    
    variables_of_interest = arrays.IntegerArray(
        label = "Variables watched by Monitors.",
        range = basic.Range(lo = 0, hi = 2, step=1),
        default = numpy.array([0], dtype=numpy.int32),
        doc = """This represents the default state-variables of this Model to be
        monitored. It can be overridden for each Monitor if desired.""")
    
    #Informational attribute, used for phase-plane and initial()
    state_variable_range = basic.Dict(
        label = "State Variable ranges [lo, hi]",
        default = {"V": numpy.array([-2.0, 4.0]),
                   "W": numpy.array([-6.0, 6.0])},
        doc = """The values for each state-variable should be set to encompass
            the expected dynamic range of that state-variable for the current 
            parameters, it is used as a mechanism for bounding random inital 
            conditions when the simulation isn't started from an explicit
            history, it is also provides the default range of phase-plane plots.""")
    
    
    def __init__(self, **kwargs):
        """
        May need to put kwargs back if we can't get them from trait...
        
        """
        
        LOG.info("%s: initing..." % str(self))
        
        super(Generic2dOscillator, self).__init__(**kwargs)
        
        self._state_variables = ["V", "W"]
        self._nvar = 2 #len(self._state_variables)
        self.cvar = numpy.array([0], dtype=numpy.int32)
        
        LOG.debug("%s: inited." % repr(self))
    
    
    def dfun(self, state_variables, coupling, local_coupling=0.0):
        """
        The fast, :math:`V`, and slow, :math:`W`, state variables are typically
        considered to represent a membrane potential and recovery variable,
        respectively. Based on equations 1 and 2 of [FH_1961]_, but relabelling
        c as :math:`\\tau` due to its interpretation as a time-scale separation,
        and adding parameters :math:`\\upsilon`, :math:`\\omega`, :math:`\\eta`,
        and :math:`\\gamma`, for flexibility, here we implement:
            
            .. math::
                \\dot{V} &= \\tau (\\omega \\, W + \\upsilon \\, V - 
                                   \\gamma \\,  \\frac{V^3}{3} + I) \\\\
                \\dot{W} &= -(\\eta \\, V - a + b \\, W) / \\tau
                
        where external currents :math:`I` provide the entry point for local and
        long-range connectivity.
        
        For strict consistency with [FH_1961]_, parameters :math:`\\upsilon`, 
        :math:`\\omega`, :math:`\\eta`, and :math:`\\gamma` should be set to 
        1.0, with :math:`a`, :math:`b`, and :math:`\\tau` set in the range 
        defined by equation 3 of [FH_1961]_:
            
            .. math::
                0 \\le b \\le 1 \\\\
                1 - 2 b / 3 \\le a \\le 1 \\\\
                \\tau^2 \\ge b
            
        The default state of these equations can be seen in the
        :ref:`Fitzhugh-Nagumo phase-plane <phase-plane-FHN>`.
        
        """
        
        V = state_variables[0, :]
        W = state_variables[1, :]
        
        #[State_variables, nodes]
        c_0 = coupling[0, :]
        
        dV = self.tau * (self.omega * W + self.upsilon * V - 
                         self.gamma * V**3.0 / 3.0 +
                         c_0 + local_coupling * V)
        
        dW = (self.a - self.eta * V - self.b * W) / self.tau
        derivative = numpy.array([dV, dW])
        
        return derivative


