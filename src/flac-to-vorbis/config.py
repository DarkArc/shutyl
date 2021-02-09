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

from typing import List

import json

class TargetConfig(object):
  def __init__(self, codec: str, bitrate: str, ext: str):
    self.codec = codec
    self.bitrate = bitrate
    self.ext = ext

class ConversionConfig(object):
  def __init__(self, converted_types: List[str], target: TargetConfig):
    self.converted_types = converted_types
    self.target = TargetConfig(**target)

class AddPrinterConfig(object):
  def __init__(self, file: bool, directory: bool):
    self.file = file
    self.directory = directory

class ConversionPrinterConfig(object):
  def __init__(self, file: bool):
    self.file = file

class ExistingPrinterConfig(object):
  def __init__(self, file: bool, directory: bool):
    self.file = file
    self.directory = directory

class RemovePrinterConfig(object):
  def __init__(self, file: bool, directory: bool):
    self.file = file
    self.directory = directory

class PrinterConfig(object):
  def __init__(self,
               add: AddPrinterConfig,
               conversion: ConversionPrinterConfig,
               existing: ExistingPrinterConfig,
               remove: RemovePrinterConfig):
    self.add = AddPrinterConfig(**add)
    self.conversion = ConversionPrinterConfig(**conversion)
    self.existing = ExistingPrinterConfig(**existing)
    self.remove = RemovePrinterConfig(**remove)

class ScriptConfig(object):
  def __init__(self, src_dir: str, dst_dir: str,
               conversion: ConversionConfig,
               printer: PrinterConfig):
    self.src_dir = src_dir
    self.dst_dir = dst_dir
    self.conversion = ConversionConfig(**conversion)
    self.printer = PrinterConfig(**printer)

def load_config(config_file):
  with open(config_file, 'r') as file_handle:
    file_content = file_handle.read()
    return ScriptConfig(**json.loads(file_content))
