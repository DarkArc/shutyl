# Copyright 2021 Wyatt Childers
#
# This file is part of shutyl.
#
# shutyl is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# shutyl is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with shutyl.  If not, see <https://www.gnu.org/licenses/>.

from .config import load_config, ScriptConfig
from .file_sync import add_files, remove_files
from .signal_monitor import SignalMonitor

import argparse
import os

from json.decoder import JSONDecodeError

def parse_args():
  # Setup the command parser
  parser = argparse.ArgumentParser(description='Create a compressed version of your music library.')
  parser.add_argument('config_file', help='the configuration file for the music library')
  parser.add_argument('-v', '--verbose', dest ='verbose', action='store_true', help='force verbose printing mode')
  parser.add_argument('--rebuild', dest='rebuild', action='store_true', help='force reconvert and copy')

  return parser.parse_args()

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

def apply_flags(args, config: ScriptConfig):
  if args.verbose:
    config.printer.make_verbose()

  if args.rebuild:
    config.force_rebuild()

def main():
  args = parse_args()

  config_file = args.config_file
  if not os.path.exists(config_file):
    print("The specified config file '{0}' could not be found.".format(config_file))
    exit(1)

  # Load the config file object
  try:
    config = load_config(config_file)
  except JSONDecodeError as parse_error:
    print("The config file is not valid json at line {0}:{1}".format(parse_error.lineno, parse_error.colno))
    exit(1)
  except TypeError as parse_error:
    print("The config file was not structured correctly. Please compare against the example config.")
    exit(1)

  # Switch the working directory the location of the config file.
  #
  # This ensures that regardless of where the command is run from
  # the program will always behave the same
  config_dir = os.path.dirname(os.path.abspath(config_file))
  os.chdir(config_dir)

  validate_config(config)
  apply_flags(args, config)

  signal_monitor = SignalMonitor()

  add_files(config, signal_monitor)
  remove_files(config, signal_monitor)
