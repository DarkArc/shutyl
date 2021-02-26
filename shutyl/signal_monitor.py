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

import signal

class SignalMonitor(object):
  def __init__(self):
    self.quit_asap = False

    signal.signal(signal.SIGINT, self.register_quit_request)
    signal.signal(signal.SIGTERM, self.register_quit_request)

  def register_quit_request(self, signum, frame):
    self.quit_asap = True
    print('Terminating gracefully...')
