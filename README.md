pyRFtelemetry
==================

Based in rfactorlcd, just provide an easy output of rfactor data to python clients


Installation
------------

The plugin source can be found in src/ and can be compiled with Visual
Studio Express. The resulting .dll has to be copied over into rFators
Plugins/ directory. This part is identical to original rFactorLCDPlugin.

Compilation: If you cannot make sense of Visual Studio projects (cannot blame you), just:
- Install the Visual Studio Community (it's free), go brew a coffee, read a book, it will take a while
- Open a console
  - type:  c:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\bin\vcvars32.bat
- on _that same console_ do not close it!
  - cd to the scr folder
  - type: cl rfactorlcd.cpp /LD
  - you should have not the .dll compiled

The rFactorLCDPlugin.ini file allows to customize the port on which
the plugin is listening, the default port is TCP/4580.


Security
--------

rfactorlcd.dll doesn't do any authentification, it will send data to
every computer that connects to port 4580.


Performance and Bandwidth
-------------------------

rFactor updates telemetry data 90 times a second and score data (lap
times, place, etc.) twice a second. rfactorlcdPlugin.dll sends that
data basically raw over the network, using around 40kB/s.


Disclaimer
----------

rfactorlcd and pyrftelemetry are homebrew tools for rFactor, 
GSC2013 and other compatible games and in no way affiliated 
with Image Space Incorporated, SimBin Studios or Reiza Studios.
