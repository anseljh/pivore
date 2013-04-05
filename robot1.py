import RPi.GPIO as io
from time import sleep
from Adafruit_MCP230xx import Adafruit_MCP230XX

LEFT    =   0
RIGHT   =   1
FRONT   =   2
BACK    =   3

GREEN_LED       = 17    # GPIO

RED_LED         = 0     # IOX
BUMPER_FRONT    = 7     # IOX

# L293 pins connected to the MCP23008 IO expander [IOX]
# left motor
L293_12EN   =   1 # TODO: PWM this for variable speed
L293_1A     =   2 # + for forward, - for back
L293_2A     =   3 # - for forward, + for back
# right motor
L293_34EN   =   4 # TODO: PWM this for variable speed
L293_3A     =   5 # + for forward, - for back
L293_4A     =   6 # - for forward, + for back

# photoresistors connected to adc
PHOTOCELL_LEFT  =   0
PHOTOCELL_RIGHT =   1
#PHOTOCELL_REAR  =   2
#PHOTOCELLS      =   dict()
#PHOTOCELLS[LEFT]    =   0
#PHOTOCELLS[RIGHT]   =   1
#PHOTOCELLS[REAR]    =   2

####################################################################
#
# Setup GPIO and its pins:
#
io.setmode(io.BCM)
io.setup(GREEN_LED, io.OUT)

####################################################################
#
# Setup MCP23008 IO expander and its pins:
#
iox = Adafruit_MCP230XX(busnum = 1, address = 0x20, num_gpios = 8)
iox.config(RED_LED, iox.OUTPUT) # red LED
iox.config(BUMPER_FRONT, iox.INPUT)
#for z in xrange(1,7):
#    iox.config(z, iox.OUTPUT)
iox.config(L293_12EN, iox.OUTPUT)
iox.config(L293_1A,   iox.OUTPUT)
iox.config(L293_2A,   iox.OUTPUT)
iox.config(L293_34EN, iox.OUTPUT)
iox.config(L293_3A,   iox.OUTPUT)
iox.config(L293_4A,   iox.OUTPUT)

####################################################################
#
# Setup MCP3008 analog-digital converter (ADC):
#
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK  = 18
SPIMISO = 23
SPIMOSI = 24
SPICS   = 25
#
# set up the SPI interface pins
io.setup(SPIMOSI, io.OUT)
io.setup(SPIMISO, io.IN)
io.setup(SPICLK, io.OUT)
io.setup(SPICS, io.OUT)

##############################################################

photomax        =   None
photomin        =   None
photomax_side   =   None

def log(s=""):
    print(s)

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin=SPICLK, mosipin=SPIMOSI, misopin=SPIMISO, cspin=SPICS):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        io.output(cspin, True)
        
        io.output(clockpin, False)  # start clock low
        io.output(cspin, False)     # bring CS low
        
        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        io.output(mosipin, True)
                else:
                        io.output(mosipin, False)
                commandout <<= 1
                io.output(clockpin, True)
                io.output(clockpin, False)
        
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                io.output(clockpin, True)
                io.output(clockpin, False)
                adcout <<= 1
                if (io.input(misopin)):
                        adcout |= 0x1
        
        io.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def control_loop():
    global photomax, photomin, photomax_side
    #log("Begin control loop")
    
    # Get sensor input
    
    # 1. Bumpers
    bump = iox.input(BUMPER_FRONT)
    
    # 2. Photocells
    lphoto = readadc(PHOTOCELL_LEFT)
    rphoto = readadc(PHOTOCELL_RIGHT)
    
    for photo in (lphoto, rphoto):              # check min/max
        if photomax is None: photomax = photo 
        if photomin is None: photomin = photo 
        if photo > photomax: photomax = photo   # check max
        if photo < photomin:                    # check min
            photomin = photo
            blink(iox, RED_LED)                 # blink red if new low
    
    last_photomax_side = photomax_side
    if lphoto > rphoto: 
        #log("L > R")
        motor_right_forward()
        motor_left_stop()
        photomax_side = LEFT
    elif lphoto < rphoto: 
        #log("L < R")
        motor_left_forward()
        motor_right_stop()
        photomax_side = RIGHT
    elif lphoto == rphoto: 
        #log("L = R")
        photomax_side = None
        all_stop()
    else: raise IOError("L ? R")
    
    # Decide what to do
    if photomax_side != last_photomax_side:
        # change in photocells
        if photomax_side is LEFT:
            log("<-- Left")
        elif photomax_side is RIGHT:
            log("Right -->")
        elif photomax_side is None:
            log(" - Equal -")
    
    
    # Perform output
    if bump:
        log("BUMP!")
        iox.output(RED_LED, True)
        backup()
        iox.output(RED_LED, False)
    else:
        iox.output(RED_LED, False)
    
    
    blink(io, GREEN_LED, 1, 0.05)
    sleep(0.25)
    #log("End control loop")

def blink(device, pin, times=1, ms=200):
    delay = ms / 1000.0
    for z in range(times):
        device.output(pin, True)
        sleep(delay)
        device.output(pin, False)
        sleep(delay)

def read_photo(adcnum=PHOTOCELL_LEFT):
    return readadc(adcnum)

def output_multiple(device, pins, value):
    for pin in pins:
        device.output(pin, value)

##############################################################
#
# MOTOR CONTROL FUNCTIONS
#
def all_stop():
    iox.output(L293_12EN, False)
    iox.output(L293_34EN, False)
    iox.output(L293_1A,   False)
    iox.output(L293_2A,   False)
    iox.output(L293_3A,   False)
    iox.output(L293_4A,   False)
def motor_left_stop():
    iox.output(L293_12EN, False)
    iox.output(L293_1A,   False)
    iox.output(L293_2A,   False)
def motor_right_stop():
    iox.output(L293_34EN, False)
    iox.output(L293_3A,   False)
    iox.output(L293_4A,   False)
def motor_left_forward():
    iox.output(L293_1A,   True)
    iox.output(L293_2A,   False)
    iox.output(L293_12EN, True)
def motor_left_back():
    iox.output(L293_1A,   False)
    iox.output(L293_2A,   True)
    iox.output(L293_12EN, True)
def motor_right_forward():
    iox.output(L293_3A,   True)
    iox.output(L293_4A,   False)
    iox.output(L293_34EN, True)
def motor_right_back():
    iox.output(L293_3A,   False)
    iox.output(L293_4A,   True)
    iox.output(L293_34EN, True)
def backup():
    """Back up for 1.5 sec and stop"""
    all_stop()
    motor_right_back()
    motor_left_back()
    sleep(1.5)
    all_stop()
def turn180():
    motor_left_forward()
    motor_right_back()

##############################################################

if __name__ == "__main__":
    log("BEGINNING ROBOT1 MAIN")
    
    log("Make sure motors are stopped!")
    all_stop()
    turn180() # TEST!
    all_stop()
    
    log("Red blink")
    log(iox)
    blink(iox, RED_LED, 2)
    
    log("Green blink")
    blink(io, GREEN_LED, 2)
    
    n = 5
    log("Reading photoresistors %d times via ADC" % n)
    reads_left = list()
    reads_right = list()
    for i in xrange(n):
        blink(iox, RED_LED)
        reads_left.append(read_photo(PHOTOCELL_LEFT))
        reads_right.append(read_photo(PHOTOCELL_RIGHT))
        sleep(0.5)
    log("Left:  %s" % reads_left)
    log("Right: %s" % reads_right)
    
    log("Reading bumper %d times" % n)
    bumps = list()
    for i in xrange(n):
        blink(iox, RED_LED)
        bumps.append(iox.input(BUMPER_FRONT))
        sleep(1)
    log(bumps)
    
    while True:
        control_loop()
    
    log("END PROGRAM")