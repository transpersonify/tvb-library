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

The Spectral datatypes. This brings together the scientific and framework
methods that are associated with the Spectral datatypes.

.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>

"""

import numpy
from tvb.basic.logger.builder import get_logger
from tvb.basic.traits import util, core, types_basic as basic
from tvb.datatypes import arrays, time_series


LOG = get_logger(__name__)


class FourierSpectrum(arrays.MappedArray):
    """
    Result of a Fourier  Analysis.
    """
    #Overwrite attribute from superclass
    array_data = arrays.ComplexArray(file_storage=core.FILE_STORAGE_EXPAND)

    source = time_series.TimeSeries(
        label="Source time-series",
        doc="Links to the time-series on which the FFT is applied.")

    segment_length = basic.Float(
        label="Segment length",
        doc="""The timeseries was segmented into equally sized blocks
            (overlapping if necessary), prior to the application of the FFT.
            The segement length determines the frequency resolution of the
            resulting spectra.""")

    windowing_function = basic.String(
        label="Windowing function",
        doc="""The windowing function applied to each time segment prior to
            application of the FFT.""")

    amplitude = arrays.FloatArray(
        label="Amplitude",
        file_storage=core.FILE_STORAGE_EXPAND)

    phase = arrays.FloatArray(
        label="Phase",
        file_storage=core.FILE_STORAGE_EXPAND)

    power = arrays.FloatArray(
        label="Power",
        file_storage=core.FILE_STORAGE_EXPAND)

    average_power = arrays.FloatArray(
        label="Average Power",
        file_storage=core.FILE_STORAGE_EXPAND)

    normalised_average_power = arrays.FloatArray(
        label="Normalised Power",
        file_storage=core.FILE_STORAGE_EXPAND)

    _frequency = None
    _freq_step = None
    _max_freq = None

    __generate_table__ = True

    def configure(self):
        """After populating few fields, compute the rest of the fields"""
        # Do not call super, because that accesses data not-chunked
        self.nr_dimensions = len(self.read_data_shape())
        for i in range(self.nr_dimensions):
            setattr(self, 'length_%dd' % (i + 1), int(self.read_data_shape()[i]))

        if self.trait.use_storage is False and sum(self.get_data_shape('array_data')) != 0:
            if self.amplitude.size == 0:
                self.compute_amplitude()
            if self.phase.size == 0:
                self.compute_phase()
            if self.power.size == 0:
                self.compute_power()
            if self.average_power.size == 0:
                self.compute_average_power()
            if self.normalised_average_power.size == 0:
                self.compute_normalised_average_power()

    def write_data_slice(self, partial_result):
        """
        Append chunk.
        """
        # self.store_data_chunk('array_data', partial_result, grow_dimension=2, close_file=False)

        self.store_data_chunk('array_data', partial_result.array_data, grow_dimension=2, close_file=False)

        partial_result.compute_amplitude()
        self.store_data_chunk('amplitude', partial_result.amplitude, grow_dimension=2, close_file=False)

        partial_result.compute_phase()
        self.store_data_chunk('phase', partial_result.phase, grow_dimension=2, close_file=False)

        partial_result.compute_power()
        self.store_data_chunk('power', partial_result.power, grow_dimension=2, close_file=False)

        partial_result.compute_average_power()
        self.store_data_chunk('average_power', partial_result.average_power, grow_dimension=2, close_file=False)

        partial_result.compute_normalised_average_power()
        self.store_data_chunk('normalised_average_power', partial_result.normalised_average_power,
                              grow_dimension=2, close_file=False)

    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance of this datatype.
        """
        summary = {"Spectral type": self.__class__.__name__,
                   "Source": self.source.title,
                   "Segment length": self.segment_length,
                   "Windowing function": self.windowing_function,
                   "Frequency step": self.freq_step,
                   "Maximum frequency": self.max_freq}
        return summary

    @property
    def freq_step(self):
        """ Frequency step size of the complex Fourier spectrum."""
        if self._freq_step is None:
            self._freq_step = 1.0 / self.segment_length
            msg = "%s: Frequency step size is %s"
            LOG.debug(msg % (str(self), str(self._freq_step)))
        return self._freq_step

    @property
    def max_freq(self):
        """ Amplitude of the complex Fourier spectrum."""
        if self._max_freq is None:
            self._max_freq = 0.5 / self.source.sample_period
            msg = "%s: Max frequency is %s"
            LOG.debug(msg % (str(self), str(self._max_freq)))
        return self._max_freq

    @property
    def frequency(self):
        """ Frequencies represented the complex Fourier spectrum."""
        if self._frequency is None:
            self._frequency = numpy.arange(self.freq_step,
                                           self.max_freq + self.freq_step,
                                           self.freq_step)
            util.log_debug_array(LOG, self._frequency, "frequency")
        return self._frequency

    def compute_amplitude(self):
        """ Amplitude of the complex Fourier spectrum."""
        self.amplitude = numpy.abs(self.array_data)
        self.trait["amplitude"].log_debug(owner=self.__class__.__name__)

    def compute_phase(self):
        """ Phase of the Fourier spectrum."""
        self.phase = numpy.angle(self.array_data)
        self.trait["phase"].log_debug(owner=self.__class__.__name__)

    def compute_power(self):
        """ Power of the complex Fourier spectrum."""
        self.power = numpy.abs(self.array_data) ** 2
        self.trait["power"].log_debug(owner=self.__class__.__name__)

    def compute_average_power(self):
        """ Average-power of the complex Fourier spectrum."""
        self.average_power = numpy.mean(numpy.abs(self.array_data) ** 2, axis=-1)
        self.trait["average_power"].log_debug(owner=self.__class__.__name__)

    def compute_normalised_average_power(self):
        """ Normalised-average-power of the complex Fourier spectrum."""
        self.normalised_average_power = (self.average_power /
                                         numpy.sum(self.average_power, axis=0))
        self.trait["normalised_average_power"].log_debug(owner=self.__class__.__name__)


class WaveletCoefficients(arrays.MappedArray):
    """
    This class bundles all the elements of a Wavelet Analysis into a single
    object, including the input TimeSeries datatype and the output results as
    arrays (FloatArray)
    """
    #Overwrite attribute from superclass
    array_data = arrays.ComplexArray()

    source = time_series.TimeSeries(label="Source time-series")

    mother = basic.String(
        label="Mother wavelet",
        default="morlet",
        doc="""A string specifying the type of mother wavelet to use,
            default is 'morlet'.""") # default to 'morlet'

    sample_period = basic.Float(label="Sample period")
    #sample_rate = basic.Integer(label = "")  inversely related

    frequencies = arrays.FloatArray(
        label="Frequencies",
        doc="A vector that maps scales to frequencies.")

    normalisation = basic.String(label="Normalisation type")
    # 'unit energy' | 'gabor'

    q_ratio = basic.Float(label="Q-ratio", default=5.0)

    amplitude = arrays.FloatArray(
        label="Amplitude",
        file_storage=core.FILE_STORAGE_EXPAND)

    phase = arrays.FloatArray(
        label="Phase",
        file_storage=core.FILE_STORAGE_EXPAND)

    power = arrays.FloatArray(
        label="Power",
        file_storage=core.FILE_STORAGE_EXPAND)

    _frequency = None
    _time = None

    __generate_table__ = True

    def configure(self):
        """After populating few fields, compute the rest of the fields"""
        # Do not call super, because that accesses data not-chunked
        self.nr_dimensions = len(self.read_data_shape())
        for i in range(self.nr_dimensions):
            setattr(self, 'length_%dd' % (i + 1), int(self.read_data_shape()[i]))

        if self.trait.use_storage is False and sum(self.get_data_shape('array_data')) != 0:
            if self.amplitude.size == 0:
                self.compute_amplitude()
            if self.phase.size == 0:
                self.compute_phase()
            if self.power.size == 0:
                self.compute_power()

    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance of this datatype.
        """
        summary = {"Spectral type": self.__class__.__name__,
                   "Source": self.source.title,
                   "Wavelet type": self.mother,
                   "Normalisation": self.normalisation,
                   "Q-ratio": self.q_ratio,
                   "Sample period": self.sample_period,
                   "Number of scales": self.frequencies.shape[0],
                   "Minimum frequency": self.frequencies[0],
                   "Maximum frequency": self.frequencies[-1]}
        return summary

    @property
    def frequency(self):
        """ Frequencies represented by the wavelet spectrogram."""
        if self._frequency is None:
            self._frequency = numpy.arange(self.frequencies.lo,
                                           self.frequencies.hi,
                                           self.frequencies.step)
            util.log_debug_array(LOG, self._frequency, "frequency")
        return self._frequency

    def compute_amplitude(self):
        """ Amplitude of the complex Wavelet coefficients."""
        self.amplitude = numpy.abs(self.array_data)

    def compute_phase(self):
        """ Phase of the Wavelet coefficients."""
        self.phase = numpy.angle(self.array_data)

    def compute_power(self):
        """ Power of the complex Wavelet coefficients."""
        self.power = numpy.abs(self.array_data) ** 2

    def write_data_slice(self, partial_result):
        """
        Append chunk.
        """
        self.store_data_chunk('array_data', partial_result.array_data, grow_dimension=2, close_file=False)

        partial_result.compute_amplitude()
        self.store_data_chunk('amplitude', partial_result.amplitude, grow_dimension=2, close_file=False)

        partial_result.compute_phase()
        self.store_data_chunk('phase', partial_result.phase, grow_dimension=2, close_file=False)

        partial_result.compute_power()
        self.store_data_chunk('power', partial_result.power, grow_dimension=2, close_file=False)


class CoherenceSpectrum(arrays.MappedArray):
    """
    Result of a NodeCoherence Analysis.
    """
    #Overwrite attribute from superclass
    array_data = arrays.FloatArray(file_storage=core.FILE_STORAGE_EXPAND)

    source = time_series.TimeSeries(
        label="Source time-series",
        doc="""Links to the time-series on which the node_coherence is
            applied.""")

    nfft = basic.Integer(
        label="Data-points per block",
        default=256,
        doc="""NOTE: must be a power of 2""")

    frequency = arrays.FloatArray(label="Frequency")

    __generate_table__ = True

    def configure(self):
        """After populating few fields, compute the rest of the fields"""
        # Do not call super, because that accesses data not-chunked
        self.configure_chunk_safe()

    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance of this datatype.
        """
        summary = {"Spectral type": self.__class__.__name__,
                   "Source": self.source.title,
                   "Number of frequencies": self.frequency.shape[0],
                   "Minimum frequency": self.frequency[0],
                   "Maximum frequency": self.frequency[-1],
                   "FFT length (time-points)": self.nfft}
        return summary

    def write_data_slice(self, partial_result):
        """
        Append chunk.
        """
        self.store_data_chunk('array_data', partial_result.array_data, grow_dimension=3, close_file=False)


class ComplexCoherenceSpectrum(arrays.MappedArray):
    """
    Result of a NodeComplexCoherence Analysis.
    """

    cross_spectrum = arrays.ComplexArray(
        label="The cross spectrum",
        file_storage=core.FILE_STORAGE_EXPAND,
        doc=""" A complex ndarray that contains the nodes x nodes cross
                spectrum for every frequency frequency and for every segment.""")

    array_data = arrays.ComplexArray(
        label="Complex Coherence",
        file_storage=core.FILE_STORAGE_EXPAND,
        doc="""The complex coherence coefficients calculated from the cross
                spectrum. The imaginary values of this complex ndarray represent the
                imaginary coherence.""")

    source = time_series.TimeSeries(
        label="Source time-series",
        doc="""Links to the time-series on which the node_coherence is
                applied.""")

    epoch_length = basic.Float(
        label="Epoch length",
        doc="""The timeseries was segmented into equally sized blocks
                (overlapping if necessary), prior to the application of the FFT.
                The segement length determines the frequency resolution of the
                resulting spectra.""")

    segment_length = basic.Float(
        label="Segment length",
        doc="""The timeseries was segmented into equally sized blocks
                (overlapping if necessary), prior to the application of the FFT.
                The segement length determines the frequency resolution of the
                resulting spectra.""")

    windowing_function = basic.String(
        label="Windowing function",
        doc="""The windowing function applied to each time segment prior to
                application of the FFT.""")

    __generate_table__ = True

    _frequency = None
    _freq_step = None
    _max_freq = None

    def configure(self):
        """After populating few fields, compute the rest of the fields"""
        # Do not call super, because that accesses data not-chunked
        self.configure_chunk_safe()

    def write_data_slice(self, partial_result):
        """
        Append chunk.
        """
        self.store_data_chunk('cross_spectrum', partial_result.cross_spectrum, grow_dimension=2, close_file=False)

        self.store_data_chunk('array_data', partial_result.array_data, grow_dimension=2, close_file=False)

    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance of this datatype.
        """
        summary = {"Spectral type": self.__class__.__name__,
                   "Source": self.source.title,
                   "Frequency step": self.freq_step,
                   "Maximum frequency": self.max_freq}
        # summary["FFT length (time-points)"] = self.fft_points
        # summary["Number of epochs"] = self.number_of_epochs
        return summary

    @property
    def freq_step(self):
        """ Frequency step size of the Complex Coherence Spectrum."""
        if self._freq_step is None:
            self._freq_step = 1.0 / self.segment_length
            msg = "%s: Frequency step size is %s"
            LOG.debug(msg % (str(self), str(self._freq_step)))
        return self._freq_step

    @property
    def max_freq(self):
        """ Maximum frequency represented in the Complex Coherence Spectrum."""
        if self._max_freq is None:
            self._max_freq = 0.5 / self.source.sample_period
            msg = "%s: Max frequency is %s"
            LOG.debug(msg % (str(self), str(self._max_freq)))
        return self._max_freq

    @property
    def frequency(self):
        """ Frequencies represented in the Complex Coherence Spectrum."""
        if self._frequency is None:
            self._frequency = numpy.arange(self.freq_step,
                                           self.max_freq + self.freq_step,
                                           self.freq_step)
        util.log_debug_array(LOG, self._frequency, "frequency")
        return self._frequency
