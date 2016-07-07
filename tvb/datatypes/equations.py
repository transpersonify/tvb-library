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

The Equation datatypes. This brings together the scientific and framework 
methods that are associated with the Equation datatypes.

.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>

"""
import json
import numpy
import numexpr
from tvb.basic.traits import core, parameters_factory, types_basic as basic
from tvb.basic.logger.builder import get_logger


LOG = get_logger(__name__)
# In how many points should the equation be evaluated for the plot. Increasing this will
# give smoother results at the cost of some performance
DEFAULT_PLOT_GRANULARITY = 1024


class Equation(basic.MapAsJson, core.Type):
    "Base class for Equation data types."

    # data

    _base_classes = ['Equation', 'FiniteSupportEquation', "DiscreteEquation",
                     "TemporalApplicableEquation", "SpatialApplicableEquation", "HRFKernelEquation",
                     # TODO: There should be a refactor of Coupling which may make these unnecessary
                     'Coupling', 'CouplingData', 'CouplingScientific', 'CouplingFramework',
                     'LinearCoupling', 'LinearCouplingData', 'LinearCouplingScientific', 'LinearCouplingFramework',
                     'SigmoidalCoupling', 'SigmoidalCouplingData', 'SigmoidalCouplingScientific',
                     'SigmoidalCouplingFramework']

    equation = basic.String(
        label="Equation as a string",
        doc="""A latex representation of the equation, with the extra
                escaping needed for interpretation via sphinx.""")

    parameters = basic.Dict(
        label="Parameters in a dictionary.",
        default={},
        doc="""Should be a list of the parameters and their meaning, Traits
                should be able to take defaults and sensible ranges from any
                traited information that was provided.""")

    # sci

    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance
        of this datatype.
        """
        summary = {"Equation type": self.__class__.__name__,
                   "equation": self.equation,
                   "parameters": self.parameters}
        return summary

    # ------------------------------ pattern -----------------------------------#
    def _get_pattern(self):
        """
        Return a discrete representation of the equation.
        """
        return self._pattern

    def _set_pattern(self, var):
        """
        Generate a discrete representation of the equation for the space
        represented by ``var``.

        The argument ``var`` can represent a distance, or effective distance,
        for each node in a simulation. Or a time, or in principle any arbitrary
        `` space ``. ``var`` can be a single number, a numpy.ndarray or a
        ?scipy.sparse_matrix? TODO: think this last one is true, need to check
        as we need it for LocalConnectivity...

        """

        self._pattern = numexpr.evaluate(self.equation, global_dict=self.parameters)

    pattern = property(fget=_get_pattern, fset=_set_pattern)

    def get_series_data(self, min_range=0, max_range=100, step=None):
        """
        NOTE: The symbol from the equation which varies should be named: var
        Returns the series data needed for plotting this equation.
        """
        if step is None:
            step = float(max_range - min_range) / DEFAULT_PLOT_GRANULARITY

        var = numpy.arange(min_range, max_range+step, step)
        var = var[numpy.newaxis, :]

        self.pattern = var
        y = self.pattern
        result = zip(var.flat, y.flat)
        return result, False

    @staticmethod
    def build_equation_from_dict(equation_field_name, submitted_data_dict, alter_submitted_dictionary=False):
        """
        Builds from the given data dictionary the equation for the specified field name.
        The dictionary should have the data collapsed.
        """
        if equation_field_name not in submitted_data_dict:
            return None

        eq_param_str = equation_field_name + '_parameters'
        eq = submitted_data_dict.get(eq_param_str)

        equation_parameters = {}
        if eq:
            if 'parameters' in eq:
                equation_parameters = eq['parameters']
            if 'parameters_parameters' in eq:
                equation_parameters = eq['parameters_parameters']

        for k in equation_parameters:
            equation_parameters[k] = float(equation_parameters[k])

        equation_type = submitted_data_dict[equation_field_name]
        equation = parameters_factory.get_traited_instance_for_name(equation_type, Equation,
                                                                    {'parameters': equation_parameters})
        if alter_submitted_dictionary:
            del submitted_data_dict[eq_param_str]
            submitted_data_dict[equation_field_name] = equation

        return equation

    @staticmethod
    def to_json(entity):
        """
        Returns the json representation of this equation.

        The representation of an equation is a dictionary with the following form:
        {'equation_type': '$equation_type', 'parameters': {'$param_name': '$param_value', ...}}
        """
        if entity is not None:
            result = {'__mapped_module': entity.__class__.__module__,
                      '__mapped_class': entity.__class__.__name__,
                      'parameters': entity.parameters}
            return json.dumps(result)
        return None

    @staticmethod
    def from_json(string):
        """
        Retrieves an instance to an equation represented as JSON.

        :param string: the JSON representation of the equation
        :returns: a `tvb.datatypes.equations_data` equation instance
        """
        loaded_dict = json.loads(string)
        if loaded_dict is None:
            return None
        modulename = loaded_dict['__mapped_module']
        classname = loaded_dict['__mapped_class']
        module_entity = __import__(modulename, globals(), locals(), [classname])
        class_entity = getattr(module_entity, classname)
        loaded_instance = class_entity()
        loaded_instance.parameters = loaded_dict['parameters']
        return loaded_instance


class TemporalApplicableEquation(Equation):
    """
    Abstract class introduced just for filtering what equations to be displayed in UI,
    for setting the temporal component in Stimulus on region and surface.
    """
    pass


class FiniteSupportEquation(TemporalApplicableEquation):
    """
    Equations that decay to zero as the variable moves away from zero. It is
    necessary to restrict spatial equation evaluated on a surface to this
    class, are . The main purpose of this class is to facilitate filtering in the UI,
    for patters on surface (stimuli surface and localConnectivity).
    """
    pass


class SpatialApplicableEquation(Equation):
    """
    Abstract class introduced just for filtering what equations to be displayed in UI,
    for setting model parameters on the Surface level.
    """
    pass


class DiscreteEquation(FiniteSupportEquation):
    """
    A special case for 'discrete' spaces, such as the regions, where each point
    in the space is effectively just assigned a value.

    """
    equation = basic.String(
        label="Discrete Equation",
        default="var",
        locked=True,
        doc="""The equation defines a function of :math:`x`""")


class Linear(TemporalApplicableEquation):
    """
    A linear equation.

    """
    equation = basic.String(
        label="Linear Equation",
        default="a * var + b",
        locked=True,
        doc=""":math:`result = a * x + b`""")

    parameters = basic.Dict(
        label="Linear Parameters",
        default={"a": 1.0,
                 "b": 0.0})


class Gaussian(SpatialApplicableEquation, FiniteSupportEquation):
    """
    A Gaussian equation.
    offset: parameter to extend the behaviour of this function
    when spatializing model parameters.

    """

    equation = basic.String(
        label="Gaussian Equation",
        default="(amp * exp(-((var-midpoint)**2 / (2.0 * sigma**2))))+offset",
        locked=True,
        doc=""":math:`(amp \\exp\\left(-\\left(\\left(x-midpoint\\right)^2 /
        \\left(2.0 \\sigma^2\\right)\\right)\\right)) + offset`""")

    parameters = basic.Dict(
        label="Gaussian Parameters",
        default={"amp": 1.0, "sigma": 1.0, "midpoint": 0.0, "offset": 0.0})


class DoubleGaussian(FiniteSupportEquation):
    """
    A Mexican-hat function approximated by the difference of Gaussians functions.

    """
    _ui_name = "Mexican-hat"

    equation = basic.String(
        label="Double Gaussian Equation",
        default="(amp_1 * exp(-((var-midpoint_1)**2 / (2.0 * sigma_1**2)))) - (amp_2 * exp(-((var-midpoint_2)**2 / (2.0 * sigma_2**2))))",
        locked=True,
        doc=""":math:`amp_1 \\exp\\left(-\\left((x-midpoint_1)^2 / \\left(2.0
        \\sigma_1^2\\right)\\right)\\right) -
        amp_2 \\exp\\left(-\\left((x-midpoint_2)^2 / \\left(2.0
        \\sigma_2^2\\right)\\right)\\right)`""")

    parameters = basic.Dict(
        label="Double Gaussian Parameters",
        default={"amp_1": 0.5, "sigma_1": 20.0, "midpoint_1": 0.0,
                 "amp_2": 1.0, "sigma_2": 10.0, "midpoint_2": 0.0})


class Sigmoid(SpatialApplicableEquation, FiniteSupportEquation):
    """
    A Sigmoid equation.
    offset: parameter to extend the behaviour of this function
    when spatializing model parameters.
    """

    equation = basic.String(
        label="Sigmoid Equation",
        default="(amp / (1.0 + exp(-1.8137993642342178 * (radius-var)/sigma))) + offset",
        locked=True,
        doc=""":math:`(amp / (1.0 + \\exp(-\\pi/\\sqrt(3.0)
            (radius-x)/\\sigma))) + offset`""")

    parameters = basic.Dict(
        label="Sigmoid Parameters",
        default={"amp": 1.0, "radius": 5.0, "sigma": 1.0, "offset": 0.0}) #"pi": numpy.pi,


class GeneralizedSigmoid(TemporalApplicableEquation):
    """
    A General Sigmoid equation.
    """

    equation = basic.String(
        label="Generalized Sigmoid Equation",
        default="low + (high - low) / (1.0 + exp(-1.8137993642342178 * (var-midpoint)/sigma))",
        locked=True,
        doc=""":math:`low + (high - low) / (1.0 + \\exp(-\\pi/\\sqrt(3.0)
            (x-midpoint)/\\sigma))`""")

    parameters = basic.Dict(
        label="Sigmoid Parameters",
        default={"low": 0.0, "high": 1.0, "midpoint": 1.0, "sigma": 0.3}) #,
    #"pi": numpy.pi})


class Sinusoid(TemporalApplicableEquation):
    """
    A Sinusoid equation.
    """

    equation = basic.String(
        label="Sinusoid Equation",
        default="amp * sin(6.283185307179586 * frequency * var)",
        locked=True,
        doc=""":math:`amp \\sin(2.0 \\pi frequency x)` """)

    parameters = basic.Dict(
        label="Sinusoid Parameters",
        default={"amp": 1.0, "frequency": 0.01}) #kHz #"pi": numpy.pi,


class Cosine(TemporalApplicableEquation):
    """
    A Cosine equation.
    """

    equation = basic.String(
        label="Cosine Equation",
        default="amp * cos(6.283185307179586 * frequency * var)",
        locked=True,
        doc=""":math:`amp \\cos(2.0 \\pi frequency x)` """)

    parameters = basic.Dict(
        label="Cosine Parameters",
        default={"amp": 1.0, "frequency": 0.01}) #kHz #"pi": numpy.pi,


class Alpha(TemporalApplicableEquation):
    """
    An Alpha function belonging to the Exponential function family.
    """

    equation = basic.String(
        label="Alpha Equation",
        default="where((var-onset) > 0, (alpha * beta) / (beta - alpha) * (exp(-alpha * (var-onset)) - exp(-beta * (var-onset))), 0.0 * var)",
        locked=True,
        doc=""":math:`(\\alpha * \\beta) / (\\beta - \\alpha) *
            (\\exp(-\\alpha * (x-onset)) - \\exp(-\\beta * (x-onset)))` for :math:`(x-onset) > 0`""")

    parameters = basic.Dict(
        label="Alpha Parameters",
        default={"onset": 0.5, "alpha": 13.0, "beta": 42.0})


class PulseTrain(TemporalApplicableEquation):
    """
    A pulse train , offset with respect to the time axis.

    **Parameters**:

    * :math:`\\tau` :  pulse width or pulse duration
    * :math:`T`     :  pulse repetition period
    * :math:`f`     :  pulse repetition frequency (1/T)
    * duty cycle    :  :math:``\\frac{\\tau}{T}`` (for a square wave: 0.5)
    * onset time    :
    """

    equation = basic.String(
        label="Pulse Train",
        default="where((var % T) < tau, amp, 0)",
        locked=True,
        doc=""":math:`\\frac{\\tau}{T}
        +\\sum_{n=1}^{\\infty}\\frac{2}{n\\pi}
        \\sin\\left(\\frac{\\pi\\,n\\tau}{T}\\right)
        \\cos\\left(\\frac{2\\pi\\,n}{T} var\\right)`.
        The starting time is halfway through the first pulse.
        The phase can be offset t with t - tau/2""")

    # onset is in milliseconds
    # T and tau are in milliseconds as well

    parameters = basic.Dict(
        default={"T": 42.0, "tau": 13.0, "amp": 1.0, "onset": 30.0},
        label="Pulse Train Parameters")

    def _get_pattern(self):
        """
        Return a discrete representation of the equation.
        """
        return self._pattern

    def _set_pattern(self, var):
        """
        Generate a discrete representation of the equation for the space
        represented by ``var``.

        The argument ``var`` can represent a distance, or effective distance,
        for each node in a simulation. Or a time, or in principle any arbitrary
        `` space ``. ``var`` can be a single number, a numpy.ndarray or a
        ?scipy.sparse_matrix? TODO: think this last one is true, need to check
        as we need it for LocalConnectivity...

        """

        # rolling in the deep ...
        onset = self.parameters["onset"]
        off = var < onset
        var = numpy.roll(var, off.sum() + 1)
        var[..., off] = 0.0
        self._pattern = numexpr.evaluate(self.equation, global_dict=self.parameters)
        self._pattern[..., off] = 0.0

    pattern = property(fget=_get_pattern, fset=_set_pattern)


class HRFKernelEquation(Equation):
    "Base class for hemodynamic response functions."
    pass


class Gamma(HRFKernelEquation):
    """
    A Gamma function for the bold monitor. It belongs to the family of Exponential functions.

    **Parameters**:


    * :math:`\\tau`      : Exponential time constant of the gamma function [seconds].
    * :math:`n`          : The phase delay of the gamma function.
    * :math: `factorial` : (n-1)!. numexpr does not support factorial yet.
    * :math: `a`         : Amplitude factor after normalization.


    **Reference**:

    .. [B_1996] Geoffrey M. Boynton, Stephen A. Engel, Gary H. Glover and David
        J. Heeger (1996). Linear Systems Analysis of Functional Magnetic Resonance
        Imaging in Human V1. J Neurosci 16: 4207-4221

    .. note:: might be filtered from the equations used in Stimulus and Local Connectivity.

    """

    _ui_name = "HRF kernel: Gamma kernel"

    # TODO: Introduce a time delay in the equation (shifts the hrf onset)
    # """:math:`h(t) = \frac{(\frac{t-\delta}{\tau})^{(n-1)} e^{-(\frac{t-\delta}{\tau})}}{\tau(n-1)!}"""
    # delta = 2.05 seconds -- Additional delay in seconds from the onset of the
    # time-series to the beginning of the gamma hrf.
    # delay cannot be negative or greater than the hrf duration.

    equation = basic.String(
        label="Gamma Equation",
        default="((var / tau) ** (n - 1) * exp(-(var / tau)) )/ (tau * factorial)",
        locked=True,
        doc=""":math:`h(var) = \\frac{(\\frac{var}{\\tau})^{(n-1)}\\exp{-(\\frac{var}{\\tau})}}{\\tau(n-1)!}`.""")

    parameters = basic.Dict(
        label="Gamma Parameters",
        default={"tau": 1.08, "n": 3.0, "factorial": 2.0, "a": 0.1})

    def _get_pattern(self):
        """
        Return a discrete representation of the equation.
        """
        return self._pattern

    def _set_pattern(self, var):
        """
        Generate a discrete representation of the equation for the space
        represented by ``var``.

        .. note: numexpr doesn't support factorial yet

        """

        # compute the factorial
        n = int(self.parameters["n"])
        product = 1
        for i in range(n - 1):
            product *= i + 1

        self.parameters["factorial"] = product
        self._pattern = numexpr.evaluate(self.equation,
                                         global_dict=self.parameters)
        self._pattern /= max(self._pattern)
        self._pattern *= self.parameters["a"]

    pattern = property(fget=_get_pattern, fset=_set_pattern)


class DoubleExponential(HRFKernelEquation):
    """
    A difference of two exponential functions to define a kernel for the bold monitor.

    **Parameters** :

    * :math:`\\tau_1`: Time constant of the second exponential function [s]
    * :math:`\\tau_2`: Time constant of the first exponential function [s].
    * :math:`f_1`  : Frequency of the first sine function [Hz].
    * :math:`f_2`  : Frequency of the second sine function [Hz].
    * :math:`amp_1`: Amplitude of the first exponential function.
    * :math:`amp_2`: Amplitude of the second exponential function.
    * :math:`a`    : Amplitude factor after normalization.


    **Reference**:

    .. [P_2000] Alex Polonsky, Randolph Blake, Jochen Braun and David J. Heeger
        (2000). Neuronal activity in human primary visual cortex correlates with
        perception during binocular rivalry. Nature Neuroscience 3: 1153-1159

    """

    _ui_name = "HRF kernel: Difference of Exponentials"

    equation = basic.String(
        label="Double Exponential Equation",
        default="((amp_1 * exp(-var/tau_1) * sin(2.*pi*f_1*var)) - (amp_2 * exp(-var/ tau_2) * sin(2.*pi*f_2*var)))",
        locked=True,
        doc=""":math:`h(var) = amp_1\\exp(\\frac{-var}{\tau_1})
        \\sin(2\\cdot\\pi f_1 \\cdot var) - amp_2\\cdot \\exp(-\\frac{var}
        {\\tau_2})*\\sin(2\\pi f_2 var)`.""")

    parameters = basic.Dict(
        label="Double Exponential Parameters",
        default={"tau_1": 7.22, "f_1": 0.03, "amp_1": 0.1,
                 "tau_2": 7.4, "f_2": 0.12, "amp_2": 0.1,
                 "a": 0.1, "pi": numpy.pi})

    def _get_pattern(self):
        """
        Return a discrete representation of the equation.
        """
        return self._pattern

    def _set_pattern(self, var):
        """
        Generate a discrete representation of the equation for the space
        represented by ``var``.

        """

        self._pattern = numexpr.evaluate(self.equation, global_dict=self.parameters)
        self._pattern /= max(self._pattern)

        self._pattern *= self.parameters["a"]

    pattern = property(fget=_get_pattern, fset=_set_pattern)


class FirstOrderVolterra(HRFKernelEquation):
    """
    Integral form of the first Volterra kernel of the three used in the
    Ballon Windekessel model for computing the Bold signal.
    This function describes a damped Oscillator.

    **Parameters** :

    * :math:`\\tau_s`: Dimensionless? exponential decay parameter.
    * :math:`\\tau_f`: Dimensionless? oscillatory parameter.
    * :math:`k_1`    : First Volterra kernel coefficient.
    * :math:`V_0` : Resting blood volume fraction.


    **References** :

    .. [F_2000] Friston, K., Mechelli, A., Turner, R., and Price, C., *Nonlinear
        Responses in fMRI: The Balloon Model, Volterra Kernels, and Other
        Hemodynamics*, NeuroImage, 12, 466 - 477, 2000.

    """

    _ui_name = "HRF kernel: Volterra Kernel"

    equation = basic.String(
        label="First Order Volterra Kernel",
        default="1/3. * exp(-0.5*(var / tau_s)) * (sin(sqrt(1./tau_f - 1./(4.*tau_s**2)) * var)) / (sqrt(1./tau_f - 1./(4.*tau_s**2)))",
        locked=True,
        doc=""":math:`G(t - t^{\\prime}) =
             e^{\\frac{1}{2} \\left(\\frac{t - t^{\\prime}}{\\tau_s} \\right)}
             \\frac{\sin\\left((t - t^{\\prime})
             \\sqrt{\\frac{1}{\\tau_f} - \\frac{1}{4 \\tau_s^2}}\\right)}
             {\\sqrt{\\frac{1}{\\tau_f} - \\frac{1}{4 \\tau_s^2}}}
             \\; \\; \\; \\; \\; \\;  for \\; \\; \\; t \\geq t^{\\prime}
             = 0 \\; \\; \\; \\; \\; \\;  for \\; \\; \\;  t < t^{\\prime}`.""")

    parameters = basic.Dict(
        label="Mixture of Gammas Parameters",
        default={"tau_s": 0.8, "tau_f": 0.4, "k_1": 5.6, "V_0": 0.02})


class MixtureOfGammas(HRFKernelEquation):
    """
    A mixture of two gamma distributions to create a kernel similar to the one used in SPM.

    >> import scipy.stats as sp_stats
    >> import numpy
    >> t = numpy.linspace(1,20,100)
    >> a1, a2 = 6., 10.
    >> lambda = 1.
    >> c      = 0.5
    >> hrf    = sp_stats.gamma.pdf(t, a1, lambda) - c * sp_stats.gamma.pdf(t, a2, lambda)

    gamma.pdf(x, a, theta) = (lambda*x)**(a-1) * exp(-lambda*x) / gamma(a)
    a                 : shape parameter
    theta: 1 / lambda : scale parameter


    **References**:

    .. [G_1999] Glover, G. *Deconvolution of Impulse Response in Event-Related BOLD fMRI*.
                NeuroImage 9, 416-429, 1999.


    **Parameters**:


    * :math:`a_{1}`       : shape parameter first gamma pdf.
    * :math:`a_{2}`       : shape parameter second gamma pdf.
    * :math:`\\lambda`    : scale parameter first gamma pdf.


    Default values are based on [G_1999]_:
    * :math:`a_{1} - 1 = n_{1} =  5.0`
    * :math:`a_{2} - 1 = n_{2} = 12.0`
    * :math:`c \\equiv a_{2}   = 0.4`

    Alternative values :math:`a_{2}=10` and :math:`c=0.5`

    NOTE: gamma_a_1 and gamma_a_2 are placeholders, the true values are
    computed before evaluating the expression, because numexpr does not
    support certain functions.

    NOTE: [G_1999]_ used a different analytical function that can be approximated
    by this difference of gamma pdfs

    """

    _ui_name = "HRF kernel: Mixture of Gammas"

    equation = basic.String(
        label="Mixture of Gammas",
        default="(l * var)**(a_1-1) * exp(-l*var) / gamma_a_1 - c * (l*var)**(a_2-1) * exp(-l*var) / gamma_a_2",
        locked=True,
        doc=""":math:`\\frac{\\lambda \\,t^{a_{1} - 1} \\,\\, \\exp^{-\\lambda \\,t}}{\\Gamma(a_{1})}
        - 0.5 \\frac{\\lambda \\,t^{a_{2} - 1} \\,\\, \\exp^{-\\lambda \\,t}}{\\Gamma(a_{2})}`.""")

    parameters = basic.Dict(
        label="Double Exponential Parameters",
        default={"a_1": 6.0, "a_2": 13.0, "l": 1.0, "c": 0.4, "gamma_a_1": 1.0, "gamma_a_2": 1.0})

    def _get_pattern(self):
        """
        Return a discrete representation of the equation.
        """
        return self._pattern

    def _set_pattern(self, var):
        """
        Generate a discrete representation of the equation for the space
        represented by ``var``.

        .. note: numexpr doesn't support gamma function

        """

        # get gamma functions
        from scipy.special import gamma as sp_gamma
        self.parameters["gamma_a_1"] = sp_gamma(self.parameters["a_1"])
        self.parameters["gamma_a_2"] = sp_gamma(self.parameters["a_2"])

        self._pattern = numexpr.evaluate(self.equation, global_dict=self.parameters)

    pattern = property(fget=_get_pattern, fset=_set_pattern)