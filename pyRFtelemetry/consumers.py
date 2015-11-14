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
import struct

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



class ArduinoRelay(DataConsumer):
    def __init__(self, client, ard_serial):
        DataConsumer.__init__(self, client)
        self.telemetry=None
        self.ard_serial=ard_serial
        self.rev_leds_thresholds = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.97, 0.985, 2]
        
    def dispatch_message(self, tag, payload):
        st=StructFactory.assemble(tag,payload)
        
        if isinstance(st, TelemetryData):
            mode=struct.pack(">B", 0)
            if st.gear >= 0:
                gear=struct.pack(">B", st.gear)
            else:
                gear=struct.pack(">B", 255)
            #in RF +z points to back of car
            speed = abs(int(st.velocity[2]*3.6))
            s1=struct.pack(">B", speed & 0x00ff)
            s2=struct.pack(">B", (speed & 0xff00)>>8)
            
            rev_fraction = st.engine_rpm/st.max_engine_rpm
            for i, rt in enumerate(self.rev_leds_thresholds):
                if rt > rev_fraction:
                    break
            led=struct.pack(">B", i)
            fuel=struct.pack(">B",int(st.fuel))
            res=struct.pack(">B", 0)
            
            dt1=struct.pack(">B", 0)
            dt2=struct.pack(">B", 0)
            dt3=struct.pack(">B", 0)
            dt4=struct.pack(">B", 0)
            dt5=struct.pack(">B", 0)

            msg= b"".join([b'\xff', mode, gear, s1, s2, led, fuel, res, dt1, dt2, dt3, dt4, dt5])
            self.ard_serial.write(msg)            
            
        if isinstance(st, InfoData):
            for field, tp in st._fields_:
                print(field, st.__getattribute__(field))
            
        if isinstance(st, list):
            if isinstance(st[0], VehicleData):
                for v in st:
                    print(v.driver_name)
                    print(v.best_lap_time)

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