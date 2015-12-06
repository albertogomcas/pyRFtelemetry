/*TM1638 Telemetry HUD
Copyright (C) 2015 Alberto Gomez-Casado <albertogomcas@gmail.com>

This a simple alternative to https://github.com/albertogomcas/pyRFtelemetry 
Instead of passing messages with telemetry and let arduino biuld the screens,
this builds the screens in the PC side
Some telemetry can be passed still

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

const int DATA_PIN=9;
const int CLOCK_PIN=8;
const int STROBE_PIN=7;

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
	char screen[8];
	byte dots;
	byte ledrevs;
	byte fuel;
	byte grip;
	byte check;
} Datagram, *pDatagram;

pDatagram pDTG;

typedef struct
{
	byte header1;
	byte header2;
	byte buttons1;
	byte buttons2; //not used
	byte analog1;
	byte analog2;
	byte check;
} UpstreamData, *pUpstreamData;

int valid = 0;

const int DATAGRAM_LENGTH=sizeof(Datagram);
byte DatagramBuffer[DATAGRAM_LENGTH];

pUpstreamData pUData;
const int UDATA_LENGTH = sizeof(UpstreamData);
byte udatabuffer[UDATA_LENGTH];

//Possible datagram types
const int HEADER1 = 0xaa;
const int HEADER2 = 0x50;
byte check = 0;
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
  pUData = (pUpstreamData) udatabuffer;
  pUData->header1 = HEADER1;
  pUData->header2 = HEADER2;
  
  pDTG = (pDatagram) DatagramBuffer;
}

void loop()
{
  	valid = Collect_Datagram();
  	if(valid){
  		Dispatch();
  		Send_Upstream();
  	}


}

void Send_Upstream()
{
	pUData->buttons1 = module.getButtons();
	// fill other fields if needed

	//add the check
	udatabuffer[UDATA_LENGTH-1] = udatabuffer[0];
	for (index=1; index<UDATA_LENGTH-1; index++){
		udatabuffer[UDATA_LENGTH-1] ^= udatabuffer[index];	
	}

	Serial.write(udatabuffer, UDATA_LENGTH);
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
          if (Serial.peek() == HEADER2)
          {
	          check = DatagramBuffer[0];
	          for (index=1; index<DATAGRAM_LENGTH; index++)
	          {
	            DatagramBuffer[index]=Serial.read();
	            // skip the last byte (check itsef)
	            if (index < DATAGRAM_LENGTH-1) check = check ^ DatagramBuffer[index];
	          }
          
	        if (DatagramBuffer[DATAGRAM_LENGTH-1] == check) //test no corrupted packet
	        	return 1; //valid
          }
        }
	}
	return 0; // no data in serial or no valid datagram
}

void Dispatch()
{
	//Always update LEDs
    if (pDTG->ledrevs == 9)
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
            module.setLEDs(leds[pDTG->ledrevs]);
            Leds_up=false;
            estado_leds=65535;
          	}

	module.setDisplayToString(pDTG->screen, pDTG->dots);
}
