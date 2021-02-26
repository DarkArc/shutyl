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

from .config import ScriptConfig, ConversionConfig, TargetConfig, PrinterConfig
from .signal_monitor import SignalMonitor

import os
import pathlib
import shutil
import subprocess
import sys
import time

from concurrent.futures import ThreadPoolExecutor
from termcolor import colored
from typing import List

# Convert src_ext to a dst_ext
def to_dst_file_ext(config: ConversionConfig, src_ext: str):
  # If the source extension is in our list of converted types, this
  # file's new extension should be target_ext
  if src_ext in config.converted_types:
    return config.target.ext

  return src_ext

# Convert src_name to dst_name
def to_dst_file_name(config: ConversionConfig, src_name: str):
  split_name = os.path.splitext(src_name)
  return "{0}{1}".format(split_name[0], to_dst_file_ext(config, split_name[1]))

# Convert dst_name to src_names
def to_src_file_names(config: ConversionConfig, dst_name: str):
  split_name = os.path.splitext(dst_name)
  dst_ext = split_name[1]

  possible_names = [dst_name]
  if dst_ext == config.target.ext:
    for ext in config.converted_types:
      possible_names.append("{0}{1}".format(split_name[0], ext))

  return possible_names

# Convert src_names to src_files
def to_src_files(src_root, src_names):
  src_files = []
  for src_name in src_names:
    src_files.append(os.path.join(src_root, src_name))
  return src_files

# Check if any of the provided src_files (still) exist
def any_srcs_exists(src_files):
  for src_file in src_files:
    if os.path.exists(src_file):
      return True

  return False

# Check if a dst_file also exists for the target conversion type
def target_also_exists(config: ConversionConfig, dst_name: str):
  target_dst_name = to_dst_file_name(config, dst_name)

  # This is what we would convert to, there can't be a converted
  # version of this file
  if target_dst_name == dst_name:
    return False

  # Unless something failed, this file would have been converted,
  # optimistically remove
  return True

# Return the stats for a particular file
def get_file_stats(file: str):
  return pathlib.Path(file).stat()

# Check if a src_file is newer than dest_file
def needs_update(src_file: str, dst_file: str):
  src_file_stats = get_file_stats(src_file)
  dst_file_stats = get_file_stats(dst_file)

  return src_file_stats.st_mtime > dst_file_stats.st_mtime

# Check if a src_file has been updated in the future
def updated_in_future(src_file: str):
  src_file_stats = get_file_stats(src_file)
  return src_file_stats.st_mtime > time.time()

# Interrogate to determine if we need to skip this file
def should_skip_file(config: ScriptConfig, src_file: str, dst_file: str):
  # If the dst_file doesn't exist, we definitely shouldn't skip this
  # file
  if not os.path.exists(dst_file):
    return False

  # If we aren't blindly rebuilding, and the dst_file exists
  # check some additional details
  if not config.blind_rebuild:
    # If the file was updated in the future, skip it
    if updated_in_future(src_file):
      return True

    # If the file doesn't need an update, skip it
    if not needs_update(src_file, dst_file):
      if config.printer.existing.file:
        print("= {0}".format(dst_file))
      return True

  # We passed the additional checks, this file should not be skipped
  return False

# Copy or convert the file src_name in src_root to dst_root with dst_name
def copy_or_convert(config: ScriptConfig, signal_monitor: SignalMonitor,
                    src_root: str, src_name: str,
                    dst_root: str, dst_name: str):
  if signal_monitor.quit_asap:
    return

  src_file = os.path.join(src_root, src_name)
  dst_file = os.path.join(dst_root, dst_name)

  # Warn on any files updated in the future, it's effectively
  # impossible to tell if this needs reconverted
  if updated_in_future(src_file):
    print(
      colored("! {0} - was updated in the future".format(src_file), 'red'),
      file=sys.stderr
    )

  # Check to see if we should skip this file
  if should_skip_file(config, src_file, dst_file):
    return

  # If the dst_file exists, and we've passed the above file skip check
  # we need to remove the file for reconversion or re-copying
  #
  # Additional note: shutil.copy2 will not overwrite existing files
  if os.path.exists(dst_file):
    os.remove(dst_file)

  # If the file name doesn't match, a conversion is implied
  if src_name != dst_name:
    if config.printer.conversion.file:
      print(colored("~ {0}".format(dst_file), 'green'))

    # Execute the conversion
    target_config = config.conversion.target
    return_code = subprocess.call(
      [
        'ffmpeg',
        '-i', src_file,               # Set the source file
        '-vn',                        # Disable video
        '-c:a', target_config.codec,  # Set the audio codec
        '-ab', target_config.bitrate, # Set the target bitrate
        dst_file                      # Set the destination file
      ],
      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )

    # Warn if the conversion didn't exit cleanly
    if return_code != 0:
      # At the time of writing the subprocess also receives the signal
      # so if we're terminating early, suppress the error message
      if not signal_monitor.quit_asap:
        print(
          colored("! {0} - file conversion did not exit cleanly".format(src_file), 'red'),
          file=sys.stderr
        )

      # Cleanup any partial or invalid file
      if os.path.exists(dst_file):
        os.remove(dst_file)
  else:
    # Copy the file preserving metadata
    if config.printer.add.file:
      print(colored("+ {0}".format(dst_file), 'green'))
    shutil.copy2(src_file, dst_file, follow_symlinks=False)

def add_files(config: ScriptConfig, signal_monitor: SignalMonitor):
  with ThreadPoolExecutor() as executor:
    for src_root, dirs, files in os.walk(config.src_dir):
      # Setup the destination directory
      dst_root = src_root.replace(config.src_dir, config.dst_dir, 1)

      for name in dirs:
        if signal_monitor.quit_asap:
          return

        # Skip hidden files
        if name.startswith('.'):
          continue

        # Create missing folders
        dst_folder = os.path.join(dst_root, name)
        if not os.path.exists(dst_folder):
          if config.printer.add.directory:
            print(colored("+ {0}".format(dst_folder), 'green'))
          os.makedirs(dst_folder)
        elif config.printer.existing.directory:
          print("= {0}".format(dst_folder))

      for src_name in files:
        if signal_monitor.quit_asap:
          return

        # Skip hidden files
        if src_name.startswith('.'):
          continue

        dst_name = to_dst_file_name(config.conversion, src_name)

        executor.submit(
          copy_or_convert,
          config, signal_monitor,
          src_root, src_name,
          dst_root, dst_name
        )

def should_remove_file(config: ConversionConfig,
                       src_files: List[str], dst_name: str):
  if not any_srcs_exists(src_files):
    return True
  if target_also_exists(config, dst_name):
    return True
  return False

def remove_files(config: ScriptConfig, signal_monitor: SignalMonitor):
  for dst_root, dirs, files in os.walk(config.dst_dir, topdown=False):
    # Setup the source directory
    src_root = dst_root.replace(config.dst_dir, config.src_dir, 1)

    # Remove destination directories that no longer exist in the source file set
    for name in dirs:
      if signal_monitor.quit_asap:
        return

      # Compatibility with syncthing
      if name == '.stfolder':
        continue

      src_folder = os.path.join(src_root, name)
      dst_folder = os.path.join(dst_root, name)
      if not os.path.exists(src_folder):
        if config.printer.remove.directory:
          print(colored("- {0}".format(dst_folder), 'cyan'))
        os.rmdir(dst_folder)

    # Remove destination files that no longer exist in the source file set
    for dst_name in files:
      if signal_monitor.quit_asap:
        return

      src_names = to_src_file_names(config.conversion, dst_name)
      src_files = to_src_files(src_root, src_names)

      dst_file = os.path.join(dst_root, dst_name)

      if should_remove_file(config.conversion, src_files, dst_name):
        if config.printer.remove.file:
          print(colored("- {0}".format(dst_file), 'cyan'))
        os.remove(dst_file)
