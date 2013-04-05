pivore
======

Code for a simple Raspberry Pi-based photovore robot!

The pivore is my first robot ever. Basic components are:
- Raspberry Pi
- Magician chassis from Sparkfun, includes 2 DC motors
- L293D motor driver
- MCP23008 I/O expander
- MCP3008 analog/digital converter
- 2 light-dependent resistors (a.k.a. photocells)
- a little bumper switch on the front
- some LEDs

It's all cobbled together on a breadboard, and the Pi is held in a vertical position 
somewhat precariously by plastic spacers. I soldered together a couple of tiny little boards to
hold the photocells up and to the side in the front of the bot.

The Pi talks to the MCP23008 I/O expander over 2-wire I2C, which it then connects to the L293D to drive 
the motors and LEDs, and also receives a digital input from the bumper switch. I used a handly library from 
Adafruit to hook up the MCP23008:
http://learn.adafruit.com/mcp230xx-gpio-expander-on-the-raspberry-pi/using-the-library

The two photocells are hooked up to the MCP3008 ADC, which is hooked up to the Pi via 4-wire SPI.
Adafruit code was again quite helpful in getting this guy hooked up:
http://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/script

When the program starts, the bot goes through some blinky LED action and tests out the photocells and the 
bumper switch. (The Pi is not hooked up to a display, obviously, so I monitor this over SSH.)
