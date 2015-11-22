#!/usr/bin/env python

# pyRFtelemetry
# Copyright (C) 2015 Alberto Gomez-Casado <albertogomcas@gmail.com>
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This client consumes telemetry data and can feed an arduino via serial port
"""

from pyRFtelemetry.consumers import ArduinoRelay
from pyRFtelemetry.RFstructs import StructFactory
import serial
import time
import matplotlib.pyplot as plt
import seaborn


with open('example_data.dat', 'br') as f:
    data = f.read()
  
tags_no_payload = [b"STSS", b'EDSS', b"STRT", b'EDRT']  
tags_payload = [b'TLMT', b'VHCL', b'SCOR', b'INFO']

recovered = []

place = 0

while place < len(data):
    if any(tag==data[place:place+4] for tag in tags_no_payload):
        place += 4
        continue
    
    if any(tag == data[place:place+4] for tag in tags_payload):
        next_place = place + 4
        while not any(tag == data[next_place: next_place+4] for tag in tags_no_payload+tags_payload):
            next_place += 4
            if next_place > len(data):
                break
        recovered.append([data[place:place+4], data[place+4:next_place]])
        place = next_place   

# separate
#telemetry = [StructFactory.assemble(tag, payload) for tag, payload in recovered if tag==b'TLMT']
#vehicles = [StructFactory.assemble(tag, payload) for tag, payload in recovered if tag==b'VHCL']
#my_vehicle = [vehicle for group in vehicles for vehicle in group if vehicle.is_player]
## plot data
#
##plt.figure()
##for field in ['delta_time', 'lap_number', 'lap_start_ET']:
##    plt.plot([getattr(t, field) for t in telemetry], label=field)
##plt.legend()
#
#plt.figure()
#for field in ['sector','current_sector1', 'last_sector1', 'best_sector1', 'current_sector2', 'last_sector2', 'best_sector2']:
#    plt.plot([getattr(v, field) for v in my_vehicle], label=field)
#plt.legend()

#
if __name__ == '__main__':   
    client = object() # fake socket
           
    ## open the serial port that your ardiono
    ## is connected to.
    ser = serial.Serial("COM3", 9600, timeout=0.1)
    try:
        consumer = ArduinoRelay(client, ser)
        for tag, payload in recovered:
            consumer.dispatch_message(tag, payload)
            time.sleep(0.01)
                
    except:
        raise
    finally:
        ser.close()