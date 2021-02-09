# Copyright 2021 Wyatt Childers
#
# This file is part of flac-to-vorbis.
#
# flac-to-vorbis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# flac-to-vorbis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with flac-to-vorbis.  If not, see <https://www.gnu.org/licenses/>.

from config import load_config, ScriptConfig
from file_sync import add_files, remove_files

import argparse
import os

def parse_config_path():
  # Setup the command parser
  parser = argparse.ArgumentParser(description='Create a compressed version of your music library.')
  parser.add_argument('config_file', help='the configuration file for the music library')

  # Parse the arguments and return the config file path string
  args = parser.parse_args()
  return args.config_file

def validate_config(config: ScriptConfig):
  # Verify src_dir and dst_dir exist
  abs_src_dir = os.path.abspath(config.src_dir)
  if not os.path.exists(abs_src_dir):
    print("The configured source directory '{0}' does not exist".format(abs_src_dir))
    exit(1)

  abs_dst_dir = os.path.abspath(config.dst_dir)
  if not os.path.exists(abs_dst_dir):
    print("The configured destination directory '{0}' does not exist".format(abs_dst_dir))
    exit(1)

if __name__ == '__main__':
  config_file = parse_config_path()
  if not os.path.exists(config_file):
    print("The specified config file '{0}' could not be found.".format(config_file))
    exit(1)

  # Load the config file object
  config = load_config(config_file)

  # Switch the working directory the location of the config file.
  #
  # This ensures that regardless of where the command is run from
  # the program will always behave the same
  config_dir = os.path.dirname(os.path.abspath(config_file))
  os.chdir(config_dir)

  validate_config(config)

  add_files(config)
  remove_files(config)
