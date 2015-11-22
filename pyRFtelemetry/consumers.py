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


from .RFstructs import StructFactory, TelemetryData, InfoData, ScoreData, VehicleData
from ctypes import Structure, c_int16, c_int8, c_uint8, c_uint16, c_byte, sizeof, memmove
import ctypes
import math

class Datagram(Structure):
    def checksum(self):
        buf = (c_byte*(sizeof(self)-1))()
        memmove(buf, ctypes.byref(self), sizeof(self)-1)
        self.check = buf[0]
        for b2 in buf[1:]:
            self.check ^= b2
        
    def serialize(self):
        self.checksum()
        return ctypes.string_at(ctypes.byref(self), ctypes.sizeof(self))

header1 = 0xaa #1010 1010
header2 = 0x50 #0101 0000 (reserved 4 bits)
tlmt_tag = 0x01
vhcl_tag = 0x02

class TelemetryDatagram(Datagram):
    #matches Arduino structs
    _fields_ = [
        ("header1", c_byte),
        ("header2", c_byte),
        ("gear", c_byte),
        ("speed", c_int16),
        ("ledrevs", c_byte),
        ("fuel", c_byte),
        ("grip", c_byte),
        ("lap", c_byte),
        ("autonomy", c_byte),
        ("check", c_byte),
    ]
    _pack_=1

class VehicleDatagram(Datagram):
    #matches Arduino structs
    _fields_ = [
        ("header1", c_byte),
        ("header2", c_byte),
        ("place", c_uint8),
        ("total_laps", c_uint8), 
        ("delta", c_int16), #time in 1/10 second, max +-25s
        ("behind", c_uint16), #time in 1/10 second, max 655s
        ("res1", c_byte),
        ("res2", c_byte),
        ("check", c_byte),
    ]
    _pack_=1

assert ctypes.sizeof(VehicleDatagram) == ctypes.sizeof(TelemetryDatagram)


class DataConsumer(object):
    def __init__(self, client):
        self.client=client

    def dispatch_message(self, tag, payload):
        raise NotImplementedError          

    def main(self):
        while True:
            data= self.client.release_data()
            for tag, payload in data.items():
                self.dispatch_message(tag, payload)

class fake_serial(object):
    def write(self, msg):
        print(msg)
        
    def close(self):
        pass


class ArduinoRelay(DataConsumer):
    def __init__(self, client, ard_serial):
        DataConsumer.__init__(self, client)
        self.ard_serial=ard_serial
        self.rev_leds_thresholds = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.97, 0.985, 2]
        self.current_lap = None
        self.lap_start_fuel = None
        self.fuel_per_lap = None
        
    def update_fuel_per_lap(self, tlmt):
        if tlmt.lap_number > 1: 
            if tlmt.lap_number != self.current_lap:
                self.fuel_per_lap = self.lap_start_fuel - tlmt.fuel
                self.lap_start_fuel = tlmt.fuel
                self.current_lap = tlmt.lap_number
                #print("Updated ", self.fuel_per_lap, self.current_lap, self.lap_start_fuel)
        else:
            if not self.lap_start_fuel and tlmt.lap_number == 1:
                self.lap_start_fuel = tlmt.fuel
                self.fuel_per_lap = 0
            
        
    def dispatch_message(self, tag, payload):
        st=StructFactory.assemble(tag,payload)
        
        if isinstance(st, TelemetryData):
            self.update_fuel_per_lap(st)
            dt = TelemetryDatagram()
            dt.header1 = header1
            dt.header2 = header2 | tlmt_tag
            dt.gear = st.gear if st.gear >= 0 else 255 
            #in RF +z points to back of car
            dt.speed = abs(int(st.velocity[2]*3.6))
          
            rev_fraction = st.engine_rpm/st.max_engine_rpm
            for ledstate, rt in enumerate(self.rev_leds_thresholds):
                if rt > rev_fraction:
                    break
            dt.ledrevs = ledstate
            dt.fuel = int(st.fuel)
            dt.lap = st.lap_number 
            dt.autonomy = int(math.floor(st.fuel/self.fuel_per_lap)) if self.fuel_per_lap else 0
            self.ard_serial.write(dt.serialize())
      
                       
        if isinstance(st, list):
            if isinstance(st[0], VehicleData):
                for v in st:
                    if v.is_player:
                        dt = VehicleDatagram()
                        dt.header1 = header1
                        dt.header2 = header2 | vhcl_tag
                        dt.place = v.place
                        #times in 1/10 of a second
                        #use max in case lap times are -1 (initial laps)
                        #and min to cap to maximum 
                        dt.total_laps = v.total_laps
                        dt.behind = min(max(int(v.time_behind_next*10), -256), 255)
                        #print(v.place, v.time_behind_next, dt.behind)
                        # TODO the bloody delta
                        dt.delta = 0
                        self.ard_serial.write(dt.serialize())


class DebugPrinter(DataConsumer):
    def __init__(self, client, stop_after=500):
        DataConsumer.__init__(self, client)
        self.last = {}
        self.stop_after = stop_after
        self.seen = 0
    
    def dispatch_message(self, tag, payload):
        st = StructFactory.assemble(tag, payload)  
        print(tag)
        self.last[tag] = (payload, st)
        self.seen +=1
        if self.seen >= self.stop_after:
            raise Exception("Raised after {} messages were dispatched".format(self.stop_after))
            
class FileDump(DataConsumer):
    def __init__(self, client, filename):
        DataConsumer.__init__(self, client)
        self.filename = filename        
        
    def dispatch_message(self, tag, payload):
        with open(self.filename, 'ba+') as f:
            f.write(tag)
            f.write(payload)
    