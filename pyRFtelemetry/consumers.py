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
        
    def dispatch_message(self, tag, payload):
        st=StructFactory.assemble(tag,payload)
        
        if isinstance(st, TelemetryData):
            self.ard_serial.write(struct.pack(">B", int(st.brake*255)))
            
            
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