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
#   The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (7:10. doi: 10.3389/fninf.2013.00010)
#
#

"""
A collection of noise related classes and functions.

Specific noises inherit from the abstract class Noise, with each instance having
its own RandomStream attribute -- which is itself a Traited wrapper of Numpy's
RandomState.

.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>
.. moduleauthor:: Paula Sanz Leon <Paula@tvb.invalid>
.. moduleauthor:: Noelia Montejo <Noelia@tvb.invalid>

"""

import numpy
from tvb.datatypes import arrays, equations
from tvb.basic.traits import types_basic as basic, core
from .common import get_logger, simple_gen_astr


LOG = get_logger(__name__)


class RandomStream(core.Type):
    """
    This class provides the ability to create multiple random streams which can
    be independently seeded or set to an explicit state.

    """
    _ui_name = "Random state"
    wraps = numpy.random.RandomState
    defaults = ((42,), {})  # for init wrapped value: wraps(*def[0], **def[1])

    init_seed = basic.Integer(
        label="A random seed",
        default=42,
        doc="""A random seed used to initialise the state of an instance of
        numpy's RandomState.""")

    def configure(self):
        """
        Run base classes configure to setup traited attributes, then initialise
        the stream's state using ``init_seed``.
        """
        super(RandomStream, self).configure()
        self.reset()

    def __str__(self):
        return simple_gen_astr(self, 'init_seed')

    # TODO how does this method work?
    def set_state(self, value):
        """
        Set the state of the random number stream based on a previously stored
        state. This is to enable consistent noise state on continuation from a
        previous simulation.

        """
        try:
            numpy.random.RandomState.set_state(self, state=value)
        except TypeError:
            msg = "%s: bad state, see numpy.random.set_state"
            LOG.error(msg % str(self))
            raise msg

    def reset(self):
        """Reset the random stream to its initial state, using initial seed."""
        numpy.random.RandomState.__init__(self.value, seed=self.init_seed)


class Noise(core.Type):
    """
    Defines a base class for noise. Specific noises are derived from this class
    for use in stochastic integrations.

    .. [KloedenPlaten_1995] Kloeden and Platen, Springer 1995, *Numerical
        solution of stochastic differential equations.*

    .. [ManellaPalleschi_1989] Manella, R. and Palleschi V., *Fast and precise
        algorithm for computer simulation of stochastic differential equations*,
        Physical Review A, Vol. 40, Number 6, 1989. [3381-3385]

    .. [Mannella_2002] Mannella, R.,  *Integration of Stochastic Differential
        Equations on a Computer*, Int J. of Modern Physics C 13(9): 1177--1194,
        2002.

    .. [FoxVemuri_1988] Fox, R., Gatland, I., Rot, R. and Vemuri, G., * Fast ,
        accurate algorithm for simulation of exponentially correlated colored
        noise*, Physical Review A, Vol. 38, Number 11, 1988. [5938-5940]


    .. #Currently there seems to be a clash betwen traits and autodoc, autodoc
    .. #can't find the methods of the class, the class specific names below get
    .. #us around this...
    .. automethod:: Noise.__init__
    .. automethod:: Noise.configure_white
    .. automethod:: Noise.generate
    .. automethod:: Noise.white
    .. automethod:: Noise.coloured

    """
    _base_classes = ['Noise', 'MultiplicativeSimple']

    #NOTE: nsig is not declared here because we use this class directly as the
    #      inital conditions noise source, and in that use the job of nsig is
    #      filled by the state_variable_range attribute of the Model.

    ntau = basic.Float(
        label=r":math:`\tau`",
        required=True,
        default=0.0, range=basic.Range(lo=0.0, hi=20.0, step=1.0),
        doc="""The noise correlation time""")

    random_stream = RandomStream(
        label="Random Stream",
        required=True,
        doc="""An instance of numpy's RandomState associated with this
        specific Noise object.""")

    dt = None
    # For use if coloured
    _E = None
    _sqrt_1_E2 = None
    _eta = None
    _h = None

    def configure(self):
        """
        Run base classes configure to setup traited attributes, then ensure that
        the ``random_stream`` attribute is properly configured.

        """
        super(Noise, self).configure()
        self.random_stream.configure()

    def __str__(self):
        return simple_gen_astr(self, 'dt ntau')

    def configure_white(self, dt, shape=None):
        """Set the time step (dt) of noise or integration time"""
        self.dt = dt
        LOG.info('White noise configured with dt=%g', self.dt)

    def configure_coloured(self, dt, shape):
        r"""
        One of the simplest forms for coloured noise is exponentially correlated
        Gaussian noise [KloedenPlaten_1995]_.

        We give the initial conditions for coloured noise using the integral
        algorith for simulating exponentially correlated noise proposed by
        [FoxVemuri_1988]_

        To start the simulation, an initial value for :math:`\eta` is needed.
        It is obtained in accord with Eqs.[13-15]:

            .. math::
                m &= \text{random number}\\
                n &= \text{random number}\\
                \eta &= \sqrt{-2D\lambda\ln(m)}\,\cos(2\pi\,n)

        where :math:`D` is standard deviation of the noise amplitude and
        :math:`\lambda = \frac{1}{\tau_n}` is the inverse of the noise
        correlation time. Then we set :math:`E = \exp{-\lambda\,\delta\,t}`
        where :math:`\delta\,t` is the integration time step.

        After that the exponentially correlated, coloured noise, is obtained:

            .. math::
                a &= \text{random number}\\
                b &= \text{random number}\\
                h &= \sqrt{-2D\lambda\,(1 - E^2)\,\ln{a}}\,\cos(2\pi\,b)\\
                \eta_{t+\delta\,t} &= \eta_{t}E + h

        """
        #TODO: Probably best to change the docstring to be consistent with the
        #      below, ie, factoring out the explicit Box-Muller.
        #NOTE: The actual implementation factors out the explicit Box-Muller,
        #      using numpy's normal() instead.
        self.dt = dt
        self._E = numpy.exp(-self.dt / self.ntau)
        self._sqrt_1_E2 = numpy.sqrt((1.0 - self._E ** 2))
        self._eta = self.random_stream.normal(size=shape)
        self._dt_sqrt_lambda = self.dt * numpy.sqrt(1.0 / self.ntau)
        LOG.info('Colored noise configured with dt=%g E=%g sqrt_1_E2=%g eta=%g & dt_sqrt_lambda=%g',
                  self.dt, self._E, self._sqrt_1_E2, self._eta, self._dt_sqrt_lambda)

    def generate(self, shape, lo=-1.0, hi=1.0):
        "Generate noise realization."
        if self.ntau > 0.0:
            noise = self.coloured(shape)
        else:
            noise = self.white(shape)
        return noise

    def coloured(self, shape):
        "Generate colored noise. [FoxVemuri_1988]_"
        self._h = self._sqrt_1_E2 * self.random_stream.normal(size=shape)
        self._eta =  self._eta * self._E + self._h
        return self._dt_sqrt_lambda * self._eta

    def white(self, shape):
        "Generate white noise."
        noise = numpy.sqrt(self.dt) * self.random_stream.normal(size=shape)
        return noise


class Additive(Noise):
    """
    Additive noise which, assuming the source noise is Gaussian with unit
    variance, will result in noise with a standard deviation of nsig.

    """

    nsig = arrays.FloatArray(
        configurable_noise=True,
        label=":math:`D`",
        required=True,
        default=numpy.array([1.0]), range=basic.Range(lo=0.0, hi=10.0, step=0.1),
        order=1,
        doc="""The noise dispersion, it is the standard deviation of the
        distribution from which the Gaussian random variates are drawn. NOTE:
        Sensible values are typically ~<< 1% of the dynamic range of a Model's
        state variables.""")

    def gfun(self, state_variables):
        r"""
        Linear additive noise, thus it ignores the state_variables.

        .. math::
            g(x) = \sqrt{2D}

        """
        g_x = numpy.sqrt(2.0 * self.nsig)
        return g_x


class Multiplicative(Noise):
    r"""
    With "external" fluctuations the intensity of the noise often depends on
    the state of the system. This results in the (general) stochastic
    differential formulation:

    .. math::
        dX_t = a(X_t)\,dt + b(X_t)\,dW_t

    for appropriate coefficients :math:`a(x)` and :math:`b(x)`, which might be
    constants.

    From [KloedenPlaten_1995]_, Equation 1.9, page 104.

    """

    nsig = arrays.FloatArray(
        configurable_noise=True,
        label=":math:`D`",
        required=True,
        default=numpy.array([1.0, ]), range=basic.Range(lo=0.0, hi=10.0, step=0.1),
        order=1,
        doc="""The noise dispersion, it is the standard deviation of the
        distribution from which the Gaussian random variates are drawn. NOTE:
        Sensible values are typically ~<< 1% of the dynamic range of a Model's
        state variables.""")

    b = equations.TemporalApplicableEquation(
        label=":math:`b`",
        default=equations.Linear(parameters={"a": 1.0, "b": 0.0}),
        doc="""A function evaluated on the state-variables, the result of which enters as the diffusion coefficient.""")

    def gfun(self, state_variables):
        """
        Scale the noise by the noise dispersion and the diffusion coefficient.
        By default, the diffusion coefficient :math:`b` is a constant.
        It reduces to the simplest scheme of a linear SDE with Multiplicative
        Noise: homogeneous constant coefficients. See [KloedenPlaten_1995]_,
        Equation 4.6, page 119.

        """
        self.b.pattern = state_variables
        g_x = numpy.sqrt(2.0 * self.nsig) * self.b.pattern
        return g_x
