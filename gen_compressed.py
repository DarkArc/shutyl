#!/bin/python3

import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

src = 'Source'
dst = 'Compressed'

supported_conversions = ['.flac', '.wav']
file_target = '.ogg'

# Convert src_ext to a dst_ext
def to_dst_file_ext(src_ext):
  # If the source extension is in our supported_conversion types, this file's new extension should be file_target
  if src_ext in supported_conversions:
    return file_target
  return src_ext

# Convert src_name to dst_name
def to_dst_file_name(src_name):
  split_name = os.path.splitext(src_name)
  return "{0}{1}".format(split_name[0], to_dst_file_ext(split_name[1]))

# Convert dst_name to src_names
def to_src_file_names(dst_name):
  split_name = os.path.splitext(dst_name)
  dst_ext = split_name[1]
  if dst_ext == file_target:
    possible_names = []
    for ext in supported_conversions:
      possible_names.append("{0}{1}".format(split_name[0], ext))
    return possible_names
  else:
    return [dst_name]

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

# Copy or convert the file src_name in src_root to dst_root with dst_name
def copy_or_convert(src_root, src_name, dst_root, dst_name):
  src_file = os.path.join(src_root, src_name)
  dst_file = os.path.join(dst_root, dst_name)

  # If the file does not exist and needs conversion, use ffmpeg, otherwise copy it
  if os.path.exists(dst_file):
    return

  # If the file name doesn't match a conversion is implied
  if src_name != dst_name:
    print("~ {0}".format(dst_file))
    subprocess.call(['ffmpeg', '-i', src_file, '-vn', '-c:a', 'libvorbis', '-ab', '320k', dst_file], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
  else:
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

      if not any_srcs_exists(src_files):
        dst_file = os.path.join(dst_root, dst_name)
        print("- {0}".format(dst_file))
        os.remove(dst_file)

add_files()
remove_files()
