/*TM1638 Telemetry HUD
Copyright (C) 2015 Alberto Gomez-Casado <albertogomcas@gmail.com>

Inspired from code of batrako http://batrako.blogspot.com

See https://github.com/albertogomcas/pyRFtelemetry for a python lib working 
with this sketch 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#define REVERSE
#ifdef REVERSE
  #include <InvertedTM1638.h>
#else
  #include <TM1638.h>
#endif

#define METRIC 1
#define ENGLISH 0

const int DATA_PIN=8;
const int CLOCK_PIN=9;
const int STROBE_PIN=7;

const byte SYSTEM=METRIC; 

#ifdef REVERSE
   InvertedTM1638 module(DATA_PIN, CLOCK_PIN, STROBE_PIN);
#else
   TM1638 module(DATA_PIN, CLOCK_PIN, STROBE_PIN);
#endif

/*Datagrams must be of the same total size*/

typedef struct
{
	byte header1;
	byte header2;
	byte gear;
	int speed;  //16 bit
	byte ledrevs;
	byte fuel;
	byte grip;
	byte lap;
	byte autonomy;
	byte check;
} TelemetryDatagram, *pTelemetryDatagram;

typedef struct
{
	byte header1;
	byte header2;
	byte place;
	byte total_laps;
	int delta; // in 1/10 second
	unsigned int behind; // in 1/10 second
	byte res1;
	byte res2;
	byte check;
} VehicleDatagram, *pVehicleDatagram;

pTelemetryDatagram pTLMT;
pVehicleDatagram pVHCL;


byte Gear,Buttons;
byte Mode_Buttons=0; 
int Speed, Fuel_Remaining;
String Velocidad, Velocidad2;
String Fuel, Fuel2;
word Vel;
const int DATAGRAM_LENGTH=sizeof(TelemetryDatagram);
byte DatagramBuffer[DATAGRAM_LENGTH];

//Possible datagram types
const int HEADER1 = 0xaa;
const int HEADER2 = 0x50;
const int HEADER2_MASK = 0xF0;
const int TLMT=0x01;
const int VHCL=0x02;
byte check = 0;
int Tag = 0;

//Possible Hud modes
const int HUD_SPEED=0;
const int HUD_FUEL=1;
const int HUD_DELTA=2;
const int HUD_PLACE=3;
const int HUD_AUTONOMY=4;
const int HUD_CLEAR=99;
short int Mode_Hud = -1;

char display[8];

byte index;

long Blink_Interval=50;
boolean Leds_up;
word estado_leds=0;
unsigned long CurrentMillis, PreviousMillis=0;
word leds [10] = {0, 1, 3, 7, 15, 31, 8223, 24607, 57375, 65535};

void setup()
{
  // Initialize serial 9600 baud
  Serial.begin(9600);
  Mode_Hud=HUD_SPEED;
  Mode_Buttons=0;
  if (sizeof(TelemetryDatagram) != sizeof(VehicleDatagram)) Serial.write("ERROR: Datagrams of different length");
  if (sizeof(TelemetryDatagram) != DATAGRAM_LENGTH) Serial.write("ERROR: Wrong DATAGRAM LENGTH");
}

void loop()
{
  	Tag = Collect_Datagram();
  	if(Tag) Manage_Buttons();
  	switch(Tag)
  		{
  			case 0: 
  				break;
  			case TLMT:
  				Dispatch_Telemetry();
  				break;
  			case VHCL:
  				Dispatch_Vehicle();
  				break;
  		}
}

void Manage_Buttons()
{
	Buttons=module.getButtons();
	switch(Buttons)
		{
	    case 1:
	    	Mode_Buttons=HUD_SPEED;
	        break;
	    case 2: 
	       	Mode_Buttons=HUD_FUEL;
	        break;
	    case 4:
	    	Mode_Buttons=HUD_AUTONOMY;
	    	break;
	    case 8:
	    	Mode_Buttons=HUD_PLACE;
	    	break;
	    case 16:
	    	Mode_Buttons=HUD_DELTA;
	    	break;
	    case 128: 
	       	Mode_Buttons=HUD_CLEAR;
	        break;
	    default:
	    	Mode_Buttons=Mode_Hud;
	    	break;
	     }
	if(Mode_Buttons != Mode_Hud) module.clearDisplay();

	Mode_Hud = Mode_Buttons;

}


int Collect_Datagram()
{
      if (Serial.available()>=DATAGRAM_LENGTH)
      {
        index=0;
        memset(DatagramBuffer, 0, sizeof(DatagramBuffer));
        DatagramBuffer[0]=Serial.read();

        if (DatagramBuffer[0]==HEADER1) 
        {
          if ((Serial.peek() & HEADER2_MASK) == HEADER2)
          {
	          check = DatagramBuffer[0];
	          for (index=1; index<DATAGRAM_LENGTH; index++)
	          {
	            DatagramBuffer[index]=Serial.read();
	            // skip the last byte (check itsef)
	            if (index < DATAGRAM_LENGTH-1) check = check ^ DatagramBuffer[index];
	          }
          
	        if (DatagramBuffer[DATAGRAM_LENGTH-1] == check) //test no corrupted packet
	        	return DatagramBuffer[1] & ~HEADER2_MASK; //the tag
	        else
	        	Serial.write(DatagramBuffer, DATAGRAM_LENGTH);
          }
        }
	}
	return 0; // no data in serial or no valid datagram
}

void Dispatch_Telemetry()
{
	pTLMT = (pTelemetryDatagram) DatagramBuffer;
	//Always update LEDs
    if (pTLMT->ledrevs == 9)
       	{
       	CurrentMillis=millis();
        if (CurrentMillis - PreviousMillis > Blink_Interval)
        	{
            PreviousMillis=CurrentMillis;
            if ( Leds_up )
            	{
            	Leds_up=false;
                module.setLEDs(65535);
                estado_leds=65535;
              	}
            else
            	{
                Leds_up=true;
                module.setLEDs(0);
                estado_leds=0;
              	}
            }
        else module.setLEDs(estado_leds); 
        }
        else
          	{
            module.setLEDs(leds[pTLMT->ledrevs]);
            Leds_up=false;
            estado_leds=65535;
          	}
          	
	//Depending of mode we may update the display
	switch (Mode_Hud)
		{
		case HUD_SPEED: 
			Display_Gear_Speed();
			break;
		case HUD_FUEL: 
			Display_Fuel_Lap();
			break;
		case HUD_AUTONOMY:
			Display_Fuel_Autonomy();
			break;
		}
}

void Dispatch_Vehicle()
{
	pVHCL = (pVehicleDatagram) DatagramBuffer;
	//Depending of mode we may update the display
	switch (Mode_Hud)
		{
		case HUD_DELTA: 
			Display_DeltaTime1();
			break;
		case HUD_PLACE:
			Display_Place_Behind();
			break;
		}	
}

void Display_Place_Behind()
{
	//displays current place and delta to car in front/back (if first)
	  sprintf(display, "P% 2u % 4u", pVHCL->place, pVHCL->behind);
	  module.setDisplayToString(display, 0b0000001, 0);
}

void Display_Gear_Speed()
{
  switch(pTLMT->gear)
  {
    case 255:
        display[0] = 'r';
        break;
    case 0:
        display[0] = 'N';
        break;
    default:
        sprintf(display, "%u", pTLMT->gear);
  }
  
  Vel=(pTLMT->speed);
  if (SYSTEM==ENGLISH)
  {
    Vel=round(Vel/1.609);
  }
  
  sprintf(display+1, "% 7u", Vel);
  module.setDisplayToString(display, 0, 0);
}

void Display_Fuel_Autonomy()
{
	if (pTLMT->lap <2) sprintf(display, "F% 3u A--", pTLMT->fuel);
	else sprintf(display, "F% 3u A%2u", pTLMT->fuel, pTLMT->autonomy);
	module.setDisplayToString(display,0,0);
}

void Display_Fuel_Lap()
	{
	 sprintf(display, "F% 3u L% 2u", pTLMT->fuel, pTLMT->lap);
	 module.setDisplayToString(display,0,0);
	}

void Display_DeltaTime1()
{
  module.setDisplayToString("to do");
}
