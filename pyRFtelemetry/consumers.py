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
import time

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
        
    def is_valid(self):
        buf = (c_byte*(sizeof(self)-1))()
        memmove(buf, ctypes.byref(self), sizeof(self)-1)
        check = buf[0]
        for b2 in buf[1:]:
            check ^= b2
        
        return True if self.check == check else False 

header1 = 0xaa #1010 1010
header2 = 0x50 #0101 0000 

class DownstreamDatagram(Datagram):
    #Matches simple arduino struct
    _fields_ = [
        ("header1", c_byte),
        ("header2", c_byte),
        ("screen", c_byte*8),
        ("dots", c_byte), 
        ("ledrevs", c_byte),
        ("fuel", c_byte), 
        ("grip", c_byte),
        ("check", c_byte),
    ]
    _pack_=1
    
    def screen_from_string(self, string):
        assert len(string) == 8
        for i, c in enumerate(string.encode('ascii')):
            self.screen[i] = c
        
    def string_from_screen(self):
        return bytes(self.screen[:]).decode('ascii')

class UpstreamDatagram(Datagram):
    #Matches simple arduino upstream struct
    _fields_ = [
        ("header1", c_byte),
        ("header2", c_byte),
        ("buttons1", c_byte),
        ("buttons2", c_byte), 
        ("analog1", c_byte),
        ("analog2", c_byte), 
        ("check", c_byte),
    ]
    _pack_=1 
    
    def from_bytes(self, buf):
        memmove(ctypes.byref(self), buf, sizeof(self))        
            

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


class ArduinoSimpleRelay(DataConsumer):
    @staticmethod
    def char_gear(gear):
        if gear == 0:
            return 'N'
        elif gear == 255:
            return 'r'
        else:
            return gear
            
    def __init__(self, client, ard_serial):
        DataConsumer.__init__(self, client)
        self.ard_serial=ard_serial
        self.rev_leds_thresholds = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.97, 0.985, 2]
        
        self.this_lap = -1
        self.personal_best = 9999
        self.previous_best = 9999

        self.mode = 'speed'
        self.manual_mode = self.mode
        self.auto_mode_start = 0
        self.auto_mode_duration = 2
        
        self.upstream = UpstreamDatagram() 
        self.downstream = DownstreamDatagram()
        self.downstream.header1 = header1
        self.downstream.header2 = header2
       

        def speed_screen(tlmt):
            screen = "{:02d} {} {:03d}".format(tlmt.lap_number,
                                              self.char_gear(tlmt.gear),
                                              abs(int(tlmt.velocity[2]*3.6))
                                              )
            dots = 0b0
            return screen, dots
            
        def gear_screen(tlmt):
            screen = "   {}    ".format(self.char_gear(tlmt.gear))
            dots = 0b0
            return screen, dots   
        
        def laptime_screen(vhl):
            screen = "t {:01d}{:02d}{:03d}".format(int(vhl.last_lap_time/60), 
                            int(vhl.last_lap_time%60), 
                            int((vhl.last_lap_time%1)*100)
                            )
            dots = 0b0010100
            print(screen)
            return screen, dots            

        def delta_lap_screen(vhl):
            if self.previous_best == 9999:
                return "d  NA   " , 0b00 
            sign = '+' if vhl.last_lap_time >= self.previous_best else '-'
            delta = abs(self.previous_best - vhl.last_lap_time)
            print('prev',self.previous_best,'pb',self.personal_best,'last', vhl.last_lap_time,'delta', delta)
            screen = "d {}{:2d}{:03d}".format(sign, 
                            int(delta), 
                            int((delta%1)*100)
                            )
            print(screen)
            dots = 0b0000100
            print(screen)
            return screen, dots               

        self.modes = {
            1:'speed',
            2:'gear',
            4:'laptime',
            8:'delta_lap',
        }
        
        self.mode_type = {
            'speed': TelemetryData,
            'gear': TelemetryData,
            'laptime': VehicleData,
            'delta_lap': VehicleData,
        }
        
        self.screens = {
            'speed': speed_screen,                                               
            'gear': gear_screen,
            'laptime': laptime_screen,
            'delta_lap': delta_lap_screen,
        }
                        

    def read_upstream(self):
        try:
            if self.ard_serial.inWaiting() >= sizeof(self.upstream):
                self.upstream.from_bytes(self.ard_serial.read(sizeof(self.upstream)))
                if self.upstream.is_valid():
                    try:
                        self.mode = self.modes[self.upstream.buttons1]
                    except KeyError:
                        pass
        except:
            raise
        
    def another_lap(self, vhl):
        print('another lap', vhl.total_laps)
        self.manual_mode = self.mode
        self.mode = 'delta_lap'
        self.auto_mode_start = time.time()
        self.this_lap = vhl.total_laps  
        if vhl.best_lap_time: 
            if 0 < vhl.best_lap_time < self.personal_best:
                self.previous_best = self.personal_best
                self.personal_best = vhl.best_lap_time
            else:
                self.previous_best = self.personal_best
        
    def dispatch_message(self, tag, payload):        
        self.read_upstream()
        curr_time = time.time()
        try:
            st=StructFactory.assemble(tag,payload)
            
            if isinstance(st, TelemetryData):
                self.update_fuel_per_lap(st)
                rev_fraction = st.engine_rpm/st.max_engine_rpm
                for ledstate, rt in enumerate(self.rev_leds_thresholds):
                    if rt > rev_fraction:
                        break
                self.downstream.ledrevs = ledstate
                self.downstream.fuel = int(st.fuel) 
                           
            if isinstance(st, list):
                if isinstance(st[0], VehicleData):
                    for v in st:
                        if v.is_player:
                            st = v
                            if self.this_lap != st.total_laps:
                                self.another_lap(st)
                            
            if isinstance(st, self.mode_type[self.mode]):
                screen, self.downstream.dots = self.screens[self.mode](st)
                self.downstream.screen_from_string(screen)
            
            self.ard_serial.write(self.downstream.serialize())

            if self.auto_mode_start:
                if curr_time - self.auto_mode_start > self.auto_mode_duration:
                    self.auto_mode_start = 0
                    self.mode = self.manual_mode

        except Exception as e:
            raise    

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
    