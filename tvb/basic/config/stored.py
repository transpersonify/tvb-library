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
Manages reading and writing settings in file

.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Bogdan Neacsa <bogdan.neacsa@codemart.ro>

"""

import os

# File keys
KEY_ADMIN_NAME = 'ADMINISTRATOR_NAME'
KEY_ADMIN_PWD = 'ADMINISTRATOR_PASSWORD'
KEY_ADMIN_EMAIL = 'ADMINISTRATOR_EMAIL'
KEY_TVB_PATH = 'TVB_PATH'
KEY_STORAGE = 'TVB_STORAGE'
KEY_MAX_DISK_SPACE_USR = 'USR_DISK_SPACE'
#During the introspection phase, it is checked if either Matlab or
#octave are installed and available trough the system PATH variable
#If so, they will be used for some analyzers
KEY_MATLAB_EXECUTABLE = 'MATLAB_EXECUTABLE'
KEY_IP = 'SERVER_IP'
KEY_PORT = 'WEB_SERVER_PORT'
KEY_PORT_MPLH5 = 'MPLH5_SERVER_PORT'
KEY_URL_WEB = 'URL_WEB'
KEY_URL_MPLH5 = 'URL_MPLH5'
KEY_SELECTED_DB = 'SELECTED_DB'
KEY_DB_URL = 'URL_VALUE'
KEY_URL_VERSION = 'URL_TVB_VERSION'
KEY_CLUSTER = 'DEPLOY_CLUSTER'
KEY_MAX_THREAD_NR = 'MAXIMUM_NR_OF_THREADS'
KEY_MAX_RANGE_NR = 'MAXIMUM_NR_OF_OPS_IN_RANGE'
KEY_MAX_NR_SURFACE_VERTEX = 'MAXIMUM_NR_OF_VERTICES_ON_SURFACE'
KEY_LAST_CHECKED_FILE_VERSION = 'LAST_CHECKED_FILE_VERSION'
KEY_LAST_CHECKED_CODE_VERSION = 'LAST_CHECKED_CODE_VERSION'
KEY_FILE_STORAGE_UPDATE_STATUS = 'FILE_STORAGE_UPDATE_STATUS'


class SettingsManager():


    def __init__(self, config_file_location):
        self.config_file_location = config_file_location
        self.stored_settings = self._read_config_file()


    def _read_config_file(self):
        """
        Get data from the configurations file in the form of a dictionary.
        Return empty dictionary if file not present.
        """
        if not os.path.exists(self.config_file_location):
            return {}

        config_dict = {}
        with open(self.config_file_location, 'r') as cfg_file:
            data = cfg_file.read()
            entries = [line for line in data.split('\n') if not line.startswith('#') and len(line.strip()) > 0]
            for one_entry in entries:
                name, value = one_entry.split('=', 1)
                config_dict[name] = value
        return config_dict


    def add_entries_to_config_file(self, input_data):
        """
        Add to the dictionary of settings already existent in the settings file.

        :param input_data: A dictionary of pairs that need to be added to the config file.
        """
        config_dict = self._read_config_file()
        if config_dict is None:
            config_dict = {}

        for entry in input_data:
            config_dict[entry] = input_data[entry]

        with open(self.config_file_location, 'w') as file_writer:
            for key in config_dict:
                file_writer.write(key + '=' + str(config_dict[key]) + '\n')

        self.stored_settings = self._read_config_file()


    def write_config_data(self, config_dict):
        """
        Overwrite anything already existent in the config file
        """
        with open(self.config_file_location, 'w') as file_writer:
            for key in config_dict:
                file_writer.write(key + '=' + str(config_dict[key]) + '\n')

        self.stored_settings = self._read_config_file()


    def get_attribute(self, key, default=None, dtype=str):
        """
        Get a cfg attribute that could also be found in the settings file.
        """
        try:
            if key in self.stored_settings:
                return dtype(self.stored_settings[key])
        except ValueError:
            ## Invalid convert operation.
            return default
        return default


    def is_first_run(self):
        return self.stored_settings is None or len(self.stored_settings) <= 2

