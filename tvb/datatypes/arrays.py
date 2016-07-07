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

The Array datatypes. This brings together the scientific and framework 
methods that are associated with the Array datatypes.

.. moduleauthor:: Stuart A. Knock <Stuart@tvb.invalid>

"""

import numpy
from tvb.basic.traits import core, types_basic as basic
from tvb.basic.traits.types_mapped import MappedType, Array
from tvb.basic.traits.exceptions import ValidationException


class BaseArray(Array):
    "Base class for array-type traits."
    def _find_summary_info(self):
        "Summarize array contents."
        summary = {"Array type": self.__class__.__name__,
                   "Shape": self.shape,
                   "Maximum": self.value.max(),
                   "Minimum": self.value.min(),
                   "Mean": self.value.mean(),
                   "Median": numpy.median(self.value)}
        return summary


class FloatArray(BaseArray):
    _ui_name = "Floating-point array"
    dtype = basic.DType(default=numpy.float64)


class IntegerArray(BaseArray):
    _ui_name = "Array of integers"
    dtype = basic.DType(default=numpy.int32)


class ComplexArray(BaseArray):
    _ui_name = "Array of complex numbers"
    dtype = basic.DType(default=numpy.complex128)
    stored_metadata = [key for key in MappedType.DEFAULT_STORED_ARRAY_METADATA if key != MappedType.METADATA_ARRAY_VAR]


class BoolArray(BaseArray):
    _ui_name = "Boolean array"
    dtype = basic.DType(default=numpy.bool)
    stored_metadata = [MappedType.METADATA_ARRAY_SHAPE]

    def _find_summary_info(self):
        summary = {"Array type": self.__class__.__name__,
                   "Shape": self.shape,
                   'Number True': self.value.sum(),
                   'Percent True': self.value.mean()*100,}
        return summary


class StringArray(BaseArray):
    _ui_name = "Array of strings"
    # if you want variable length strings, you must use dtype=object
    # otherwise, must specify max lenth as 'na' where n is integer,
    # e.g. dtype='100a' for a string w/ max len 100 characters.
    dtype = None
    stored_metadata = [MappedType.METADATA_ARRAY_SHAPE]
    def _find_summary_info(self):
        summary = {"Array type": self.__class__.__name__,
                   "Shape": self.shape}
        return summary


class PositionArray(FloatArray):
    _ui_name = "Array of positions"

    coordinate_system = basic.String(label="Coordinate system",
                                     default="cartesian",
                                     doc="""The coordinate system used to specify the positions.
                                     Eg: 'spherical', 'polar'""")

    coordinate_space = basic.String(label="Coordinate space",
                                    default="None",
                                    doc="The standard space the positions are in, eg, 'MNI', 'colin27'")


class OrientationArray(FloatArray):
    _ui_name = "Array of orientations"
    coordinate_system_or = basic.String(label="Coordinate system",
                                        default="cartesian")


class IndexArray(BaseArray):
    _ui_name = "Index array"
    target = Array(label="Indexed array",
                   file_storage=core.FILE_STORAGE_NONE,
                   doc="A link to the array that the indices index.")


class MappedArray(MappedType):
    "An array stored in the database."
    KEY_SIZE = "size"
    KEY_OPERATION = "operation"

    title = basic.String
    label_x, label_y = basic.String, basic.String
    aggregation_functions = basic.JSONType(required=False)
    dimensions_labels = basic.JSONType(required=False)
    nr_dimensions, length_1d, length_2d, length_3d, length_4d = [basic.Integer] * 5
    array_data = Array()

    __generate_table__ = True

    def _find_summary_info(self):
        """
        Gather scientifically interesting summary information from an instance of this datatype.
        """
        summary = {"Title:": self.title,
                   "Dimensions:": self.dimensions_labels}
        summary.update(self.get_info_about_array('array_data'))
        return summary

    @property
    def display_name(self):
        """
        Overwrite from superclass and add title field
        """
        previous = super(MappedArray, self).display_name
        if previous is None:
            return str(self.title)
        return str(self.title) + " " + previous

    @property
    def shape(self):
        """
        Shape for current wrapped NumPy array.
        """
        return self.array_data.shape

    def configure_chunk_safe(self):
        """ Configure part which is chunk safe"""
        data_shape = self.get_data_shape('array_data')
        self.nr_dimensions = len(data_shape)
        for i in range(min(self.nr_dimensions, 4)):
            setattr(self, 'length_%dd' % (i + 1), int(data_shape[i]))

    def configure(self):
        """After populating few fields, compute the rest of the fields"""
        super(MappedArray, self).configure()
        if not isinstance(self.array_data, numpy.ndarray):
            return
        self.nr_dimensions = len(self.array_data.shape)
        for i in range(min(self.nr_dimensions, 4)):
            setattr(self, 'length_%dd' % (i + 1), self.array_data.shape[i])

    @staticmethod
    def accepted_filters():
        filters = MappedType.accepted_filters()
        filters.update({'datatype_class._nr_dimensions': {'type': 'int', 'display': 'Dimensionality',
                                                          'operations': ['==', '<', '>']},
                        'datatype_class._length_1d': {'type': 'int', 'display': 'Shape 1',
                                                      'operations': ['==', '<', '>']},
                        'datatype_class._length_2d': {'type': 'int', 'display': 'Shape 2',
                                                      'operations': ['==', '<', '>']}})
        return filters

    def reduce_dimension(self, ui_selected_items):
        """
        ui_selected_items is a dictionary which contains items of form:
        '$name_$D : [$gid_$D_$I,..., func_$FUNC]' where '$D - int dimension', '$gid - a data type gid',
        '$I - index in that dimension' and '$FUNC - an aggregation function'.

        If the user didn't select anything from a certain dimension then it means that the entire
        dimension is selected
        """

        #The fields 'aggregation_functions' and 'dimensions' will be of form:
        #- aggregation_functions = {dimension: agg_func, ...} e.g.: {0: sum, 1: average, 2: none, ...}
        #- dimensions = {dimension: [list_of_indexes], ...} e.g.: {0: [0,1], 1: [5,500],...}
        dimensions, aggregation_functions, required_dimension, shape_restrictions = \
            self.parse_selected_items(ui_selected_items)

        if required_dimension is not None:
            #find the dimension of the resulted array
            dim = len(self.shape)
            for key in aggregation_functions.keys():
                if aggregation_functions[key] != "none":
                    dim -= 1
            for key in dimensions.keys():
                if (len(dimensions[key]) == 1 and
                    (key not in aggregation_functions
                     or aggregation_functions[key] == "none")):
                    dim -= 1
            if dim != required_dimension:
                self.logger.debug("Dimension for selected array is incorrect")
                raise ValidationException("Dimension for selected array is incorrect!")

        result = self.array_data
        full = slice(0, None)
        cut_dimensions = 0
        for i in xrange(len(self.shape)):
            if i in dimensions.keys():
                my_slice = [full for _ in range(i - cut_dimensions)]
                if len(dimensions[i]) == 1:
                    my_slice.extend(dimensions[i])
                    cut_dimensions += 1
                else:
                    my_slice.append(dimensions[i])
                result = result[tuple(my_slice)]
            if i in aggregation_functions.keys():
                if aggregation_functions[i] != "none":
                    result = eval("numpy." + aggregation_functions[i] + "(result,axis=" + str(i - cut_dimensions) + ")")
                    cut_dimensions += 1

        #check that the shape for the resulted array respects given conditions
        result_shape = result.shape
        for i in xrange(len(result_shape)):
            if i in shape_restrictions:
                flag = eval(str(result_shape[i]) + shape_restrictions[i][self.KEY_OPERATION] +
                            str(shape_restrictions[i][self.KEY_SIZE]))
                if not flag:
                    msg = ("The condition is not fulfilled: dimension "
                           + str(i + 1) + " "
                           + shape_restrictions[i][self.KEY_OPERATION] + " "
                           + str(shape_restrictions[i][self.KEY_SIZE]) +
                           ". The actual size of dimension " + str(i + 1)
                           + " is " + str(result_shape[i]) + ".")
                    self.logger.debug(msg)
                    raise ValidationException(msg)

        if required_dimension is not None and 1 <= required_dimension != len(result.shape):
            self.logger.debug("Dimensions of the selected array are incorrect")
            raise ValidationException("Dimensions of the selected array are incorrect!")

        return result

    def parse_selected_items(self, ui_selected_items):
        """
        Used for parsing the user selected items.

        ui_selected_items is a dictionary which contains items of form:
        'name_D : [gid_D_I,..., func_FUNC]' where 'D - dimension', 'gid - a data type gid',
        'I - index in that dimension' and 'FUNC - an aggregation function'.
        """
        expected_shape_str = ''
        operations_str = ''
        dimensions = dict()
        aggregation_functions = dict()
        required_dimension = None
        for key in ui_selected_items.keys():
            split_array = str(key).split("_")
            current_dim = split_array[len(split_array) - 1]
            list_values = ui_selected_items[key]
            if list_values is None or len(list_values) == 0:
                list_values = []
            elif not isinstance(list_values, list):
                list_values = [list_values]
            for item in list_values:
                if str(item).startswith("expected_shape_"):
                    expected_shape_str = str(item).split("expected_shape_")[1]
                elif str(item).startswith("operations_"):
                    operations_str = str(item).split("operations_")[1]
                elif str(item).startswith("requiredDim_"):
                    required_dimension = int(str(item).split("requiredDim_")[1])
                elif str(item).startswith("func_"):
                    agg_func = str(item).split("func_")[1]
                    aggregation_functions[int(current_dim)] = agg_func
                else:
                    str_array = str(item).split("_")
                    if int(str_array[1]) in dimensions:
                        dimensions[int(str_array[1])].append(int(str_array[2]))
                    else:
                        dimensions[int(str_array[1])] = [int(str_array[2])]
        return dimensions, aggregation_functions, required_dimension, self._parse_expected_shape(expected_shape_str,
                                                                                                 operations_str)

    def _parse_expected_shape(self, expected_shape_str='', operations_str=''):
        """
        If we have the inputs of form: expected_shape='x,512,x' and operations='x,&lt;,x'.
        The result will be: {1: {'size':512, 'operation':'<'}}
        """
        result = {}
        if len(expected_shape_str.strip()) == 0 or \
           len(operations_str.strip()) == 0:
            return result

        shape_array = str(expected_shape_str).split(",")
        op_array = str(operations_str).split(",")

        operations = self._get_operations()
        for i in xrange(len(shape_array)):
            if str(shape_array[i]).isdigit() and i < len(op_array) and op_array[i] in operations:
                result[i] = {self.KEY_SIZE: int(shape_array[i]),
                             self.KEY_OPERATION: operations[op_array[i]]}
        return result

    def read_data_shape(self):
        """ Expose shape read on field 'array_data' """
        return self.get_data_shape('array_data')

    def read_data_slice(self, data_slice):
        """ Expose chunked-data access. """
        return self.get_data('array_data', data_slice)

    @staticmethod
    def _get_operations():
        """Return accepted operations"""
        operations = {'&lt;': '<',
                      '&gt;': '>',
                      '&ge;': '>=',
                      '&le;': '<=',
                      '==': '=='}
        return operations

