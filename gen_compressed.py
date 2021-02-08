#!/bin/python3

import os
import pathlib
import shutil
import subprocess

from concurrent.futures import ThreadPoolExecutor

# Configuration
src = 'Source'
dst = 'Compressed'

supported_conversions = ['.flac', '.wav']
target_codec = 'libvorbis'
target_bitrate = '320k'
target_ext = '.ogg'

# Convert src_ext to a dst_ext
def to_dst_file_ext(src_ext):
  # If the source extension is in our supported_conversion types, this
  # file's new extension should be target_ext
  if src_ext in supported_conversions:
    return target_ext
  return src_ext

# Convert src_name to dst_name
def to_dst_file_name(src_name):
  split_name = os.path.splitext(src_name)
  return "{0}{1}".format(split_name[0], to_dst_file_ext(split_name[1]))

# Convert dst_name to src_names
def to_src_file_names(dst_name):
  split_name = os.path.splitext(dst_name)
  dst_ext = split_name[1]

  possible_names = [dst_name]
  if dst_ext == target_ext:
    for ext in supported_conversions:
      possible_names.append("{0}{1}".format(split_name[0], ext))

  return possible_names

# Convert src_nmaes to src_files
def to_src_files(src_root, src_names):
  src_files = []
  for src_name in src_names:
    src_files.append(os.path.join(src_root, src_name))
  return src_files

# Check if any of the provided src_files (still) exsits
def any_srcs_exists(src_files):
  for src_file in src_files:
    if os.path.exists(src_file):
      return True

  return False

# Check if a dst_file also exists for the target conversion type
def target_also_exists(dst_name):
  target_dst_name = to_dst_file_name(dst_name)

  # This is what we would convert to, there can't be a converted
  # version of this file
  if target_dst_name == dst_name:
    return False

  # Unless something failed, this file would have been converted,
  # optimistically remove
  return True

# Return the stats for a particular file
def get_file_stats(file):
  return pathlib.Path(file).stat()

# Check if a src_file is newer than dest_file
def needs_update(src_file, dst_file):
  if not os.path.exists(dst_file):
    return True

  src_file_stats = get_file_stats(src_file)
  dst_file_stats = get_file_stats(dst_file)

  return src_file_stats.st_mtime > dst_file_stats.st_mtime

# Copy or convert the file src_name in src_root to dst_root with dst_name
def copy_or_convert(src_root, src_name, dst_root, dst_name):
  src_file = os.path.join(src_root, src_name)
  dst_file = os.path.join(dst_root, dst_name)

  # If the file doesn't need an update, skip it
  if not needs_update(src_file, dst_file):
    return

  # If the file name doesn't match a conversion is implied
  if src_name != dst_name:
    # Use ffmpeg to perform a conversion
    print("~ {0}".format(dst_file))
    subprocess.call(
      [
        'ffmpeg',
        '-i', src_file,        # Set the source file
        '-vn',                 # Disable video
        '-c:a', target_codec,  # Set the audio codec
        '-ab', target_bitrate, # Set the target bitrate
        dst_file               # Set the destination file
      ],
      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL
    )
  else:
    # Copy the file preserving metadata
    print("+ {0}".format(dst_file))
    shutil.copy2(src_file, dst_file, follow_symlinks=False)

def add_files():
  with ThreadPoolExecutor() as executor:
    futures = []

    for src_root, dirs, files in os.walk(src):
      # Setup the destination directory
      dst_root = src_root.replace(src, dst, 1)

      for name in dirs:
        # Skip hidden files
        if name.startswith('.'):
          continue

        # Create missing folders
        dst_folder = os.path.join(dst_root, name)
        if not os.path.exists(dst_folder):
          print("+ {0}".format(dst_folder))
          os.makedirs(dst_folder)

      for src_name in files:
        # Skip hidden files
        if src_name.startswith('.'):
          continue

        dst_name = to_dst_file_name(src_name)

        executor.submit(
          copy_or_convert,
          src_root, src_name,
          dst_root, dst_name
        )

def remove_files():
  for dst_root, dirs, files in os.walk(dst):
    # Setup the source directory
    src_root = dst_root.replace(dst, src, 1)

    # Remove any directories that (no longer) exist in the source file set
    for name in dirs:
      # Compatibility with syncthing
      if name == '.stfolder':
        continue

      src_folder = os.path.join(src_root, name)
      dst_folder = os.path.join(dst_root, name)
      if not os.path.exists(src_folder):
        print("- {0}".format(dst_folder))
        os.removedirs(dst_folder)

    # Remove any files that (no longer) exist in the source file set
    for dst_name in files:
      src_names = to_src_file_names(dst_name)
      src_files = to_src_files(src_root, src_names)

      dst_file = os.path.join(dst_root, dst_name)

      if not any_srcs_exists(src_files) or target_also_exists(dst_name):
        print("- {0}".format(dst_file))
        os.remove(dst_file)

add_files()
remove_files()
