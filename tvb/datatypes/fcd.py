# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
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
Adapter that uses the traits module to generate interfaces for ... Analyzer.

.. moduleauthor:: Francesca Melozzi <france.melozzi@gmail.com>
.. moduleauthor:: Marmaduke Woodman <mmwoodman@gmail.com>

"""

from tvb.basic.logger.builder import get_logger

import tvb.basic.traits.core as core
import tvb.basic.traits.types_basic as basic
import tvb.datatypes.arrays as arrays
import tvb.datatypes.time_series as time_series



LOG = get_logger(__name__)

class Fcd(arrays.MappedArray):

    array_data = arrays.FloatArray(file_storage=core.FILE_STORAGE_DEFAULT)

    source = time_series.TimeSeries(
        label="Source time-series",
        doc="Links to the time-series on which FCD is calculated.")

    sw = basic.Float(
        label="Sliding window length (ms)",
        default=120000,
        doc="""Length of the time window used to divided the time series.
                FCD matrix is calculated in the following way: the time series is divided in time window of fixed length and with an overlapping of fixed length.
                The datapoints within each window, centered at time ti, are used to calculate FC(ti) as Pearson correlation.
                The ij element of the FCD matrix is calculated as the Pearson correlation between FC(ti) and FC(tj) arranged in a vector.""")

    sp = basic.Float(
        label="Spanning between two consecutive sliding window (ms)",
        default=2000,
        doc="""Spanning= (time windows length)-(overlapping between two consecutive time window).
                FCD matrix is calculated in the following way: the time series is divided in time window of fixed length and with an overlapping of fixed length.
                The datapoints within each window, centered at time ti, are used to calculate FC(ti) as Pearson correlation.
                The ij element of the FCD matrix is calculated as the Pearson correlation between FC(ti) and FC(tj) arranged in a vector""")

    labels_ordering = basic.List(
        label="Dimension Names",
        default=["Time", "Time", "State Variable", "Mode"],
        doc="""List of strings representing names of each data dimension""")

    __generate_table__ = True

    def configure(self):
        """After populating few fields, compute the rest of the fields"""
        # Do not call super, because that accesses data not-chunked
        self.nr_dimensions = len(self.read_data_shape())
        for i in range(self.nr_dimensions):
            setattr(self, 'length_%dd' % (i + 1), int(self.read_data_shape()[i]))


    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance of this datatype.
        """
        summary = {"FCD type": self.__class__.__name__,
                   "Source": self.source.title,
                   "Dimensions": self.labels_ordering}

        summary.update(self.get_info_about_array('array_data'))
        return summary

