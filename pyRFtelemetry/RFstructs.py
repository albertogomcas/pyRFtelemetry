#!/usr/bin/env python

# pyRFtelemetry structures definition
# Copyright (C) 2015 Alberto Gomez-Casado <albertogomcas@gmail.com>
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

from ctypes import Structure, c_int, c_uint8, c_float, c_char, c_short, c_byte, sizeof
from .binary_decoder import BinaryDecoder

class StructFactory(object):
    @staticmethod
    def assemble(tag, payload):                  
        if tag == b"TLMT":
            return TelemetryData.from_buffer_copy(payload)
        elif tag == b"SCOR":
            return ScoreData.from_buffer_copy(payload)
        elif tag == b"INFO":
            msg = BinaryDecoder(payload) 
            track_name=msg.read_string()
            player_name = msg.read_string()
            prl_file = msg.read_string()
            infostruct = InfoData.from_buffer_copy(msg.data[msg.offset:])
            #hook the variable length part (strings)
            infostruct.track_name = track_name
            infostruct.player_name = player_name
            infostruct.prl_file = prl_file
            return infostruct
            
        elif tag == b"STSS":
            print("[start_session]")
        elif tag == b"EDSS":
            print("[end_session]")
        elif tag == b"STRT":
            print("[start_realtime]")
        elif tag == b"EDRT":
            print("[end_realtime]")
        elif tag == b"VHCL":           
            msg = BinaryDecoder(payload)
            num_vehicles = msg.read_int()
            #print("info.mNumVehicles", num_vehicles)
            
            vehicles = []
    
            for i in range(0, num_vehicles):               
                is_player = msg.read_char()
                player_control = msg.read_char()
                driver_name = msg.read_string()
                vehicle_name = msg.read_string()
                vehicle_class = msg.read_string()
                
                vinfo = VehicleData.from_buffer_copy(
                    msg.data[msg.offset : msg.offset+sizeof(VehicleData)]
                    )
                #hook the variable length part (strings)
                vinfo.is_player = is_player
                vinfo.player_control = player_control
                vinfo.driver_name = driver_name
                vinfo.vehicle_name = vehicle_name
                vinfo.vehicle_class = vehicle_class
                #fix the offset of the decoder
                msg.offset+=sizeof(VehicleData)
                
                vehicles.append(vinfo)
                
            return vehicles
            
        else:
            print("error: unknown tag: {}".format(tag))           
        return None

class EnhancedStructure(Structure):
    def numpyfy(self):
        pass


class WheelData(Structure):
    _fields_ = [
        ("rotation", c_float),
        ("suspension_deflection", c_float),
        ("ride_height", c_float),
        ("tire_load", c_float),
        ("lateral_force", c_float),
        ("grip_fraction", c_float),
        ("brake_temp", c_float),
        ("pressure", c_float),
        ("temperatures", c_float*3),
        ("wear", c_float),
        ("surface_type", c_char),
        ("flat", c_char),
        ("detached", c_char)
        ]
    _pack_=1

class TelemetryData(Structure):
    _fields_ = [
        ("delta_time", c_float),
        ("lap_number", c_int),
        ("lap_start_ET", c_float),
        ("position", c_float*3),
        ("velocity", c_float*3),
        ("acceleration", c_float*3),
        ("origx", c_float*3),
        ("origy", c_float*3),
        ("origz", c_float*3),
        ("local_rotation", c_float*3),
        ("local_rotation_accel", c_float*3),
        ("gear", c_int),
        ("engine_rpm", c_float),
        ("max_engine_rpm", c_float),
        ("clutch_rpm", c_float),
        ("fuel", c_float),
        ("water_temp", c_float),
        ("oil_temp", c_float),
        ("throttle", c_float),
        ("brake", c_float),
        ("steering", c_float),
        ("clutch", c_float),
        ("steering_arm_force", c_float),
        ("scheduled_stops", c_char),
        ("overheating", c_char),
        ("detached", c_char),
        ("dent", c_char*8),
        ("last_impact_ET", c_float),
        ("last_impact_magnitude", c_float),
        ("last_impact_pos", c_float*3),
        ("wheels", WheelData*4)
        ]
    _pack_=1

class VehicleData(Structure):
    #variable length strings are hooked later
    _fields_ = [
    ("total_laps" , c_short),
    ("sector", c_uint8),
    ("finish_status", c_char),
    ("lap_distance", c_float),
    ("path_lateral", c_float),
    ("track_edge", c_float),
    ("in_pits" , c_char),
    ("place", c_byte),
    ("time_behind_next", c_float),
    ("laps_behind_next", c_int),
    ("time_behind_leader", c_float),
    ("laps_behind_leader", c_int),
    ("best_sector1", c_float),
    ("best_sector2", c_float),
    ("best_lap_time", c_float),
    ("last_sector1", c_float),
    ("last_sector2", c_float),
    ("last_lap_time", c_float),
    ("current_sector1", c_float),
    ("current_sector2", c_float),
    ("num_pitstops", c_short),
    ("num_penalties", c_short),
    ("lap_start_ET", c_float),
    ("position", c_float*3),
    ("velocity", c_float*3),
    ("acceleration", c_float*3),
    ("origx", c_float*3),
    ("origy", c_float*3),
    ("origz", c_float*3),
    ("local_rotation", c_float*3),
    ("local_rotation_accel", c_float*3)       
    ]
    _pack_=1
    

    
class ScoreData(Structure):
    _fields_ = [
        ("game_phase", c_char),
        ("yellow_flag", c_char),
        ("sector_flag0", c_char),
        ("sector_flag1", c_char),
        ("sector_flag2", c_char),
        ("start_light", c_char),
        ("num_red_lights", c_char),
        ("in_realtime", c_char),
        ("session", c_int),
        ("current_ET", c_float),
        ("ambient_temp", c_float),
        ("track_temp", c_float),
        ("dark_cloud", c_float),
        ("raining", c_float),
        ("wind", c_float*3),
        ("on_path_wet", c_float),
        ("off_path_wet", c_float)
        ]
    _pack_=1
    
class InfoData(Structure):
    #variable length strings are hooked later
    _fields_ = [
        ("end_ET", c_float),
        ("max_laps", c_int),
        ("lap_distance", c_float)
    ]
    _pack_=1
    

