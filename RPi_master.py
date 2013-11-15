#// Arduino I2C Wire master version 0.2 
#// by Racer993 <http://raspberrypi4dummies.wordpress.com/>

#// Turns the Raspberry Pi into a I2C master device using I2C-tools. 
#// send commands to the I2C Arduino slave for configuring pins, 
#// read and write to pins via a simple instruction set.

#// the i2c-tools are required use "sudo apt-get install i2c-tools"
#// the I2C slave software must be installed on the Arduino

#// Supported instructions
#// pinMode             = setPin(device, pinnumber, INPUT/OUTPUT/INPUT_PULLUP)
#// digitalWrite        = writePin(device,pinnumber,HIGH/LOW)
#// analogWrite (=PWM)  = analogWritePin(device,pinnumber,0-255)
#// digital/analog read = getStatus(device) reads all the digital/analog pins
#// digital/analog read = pinValue gets the value for a single pin

#// A0 - analog read / digital write
#// A1 - analog read / digital write
#// A2 - analog read / digital write
#// A3 - analog read / digital write
#// A4 - IN USE as SDA
#// A5 - IN USE as SCL

#//  1 - digital read / write + RX
#//  2 - digital read / write + TX  + Interrupt
#//  3 - digital read / write + PWM + Interrupt
#//  4 - digital read / write
#//  5 - digital read / write + PWM
#//  6 - digital read / write + PWM
#//  7 - digital read / write
#//  8 - digital read / write
#//  9 - digital read / write + PWM
#// 10 - digital read / write + PWM + SPI - SS
#// 11 - digital read / write + PWM + SPI - MOSI
#// 12 - digital read / write +       SPI - MISO
#// 13 - digital read / write + LED + SPI - SCK

#// HOW TO USE

#// sending commands

#// general: all commands must be 7 bytes long + 1 ending byte

#// 1) to set the pinMode write a message with 7 characters on I2C bus to the arduino
#// first character = S for set pinMode
#// second & third character are pin ID 00 - 13 for digital pins & A0 - A3 for analog pins
#// fourth character is to set the mode I for INPUT, O for OUTPUT, P for INPUT_PULLUP
#// character 5,6,7 are not used, set to 000
#// e.g. S13O000 Sets pin 13 to an OUTPUT

#// 2) to turn the pin on or off write a message with 7 characters on I2C bus to the arduino
#// first character = W for digitalWrite
#// second & third character are pin ID 00 - 13 for digital pins & A0 - A3 for analog pins
#// fourth character is to turn off or on H for HIGH and L for LOW
#// character 5,6,7 are not used, set to 000
#// e.g. W13H000 turns pin 13 on

#// 3) to turn use PWM write a message with 7 characters on I2C bus to the arduino
#// first character = A for analogWrite
#// second & third character are pin ID 00 - 13 for digital pins & A0 - A3 for analog pins
#// forth character is not used, set to X
#// fifth - seventh character are used to write the PWM cycle (000-255)
#// e.g. A05X120 performs an analogWrite on digital pin 5 with a PWM cycle of 120

#// 4) to get a status with pin readings send Wire.requestFrom(device, #chars = 30)
#// the arduino will send back 30 chars 
#// char 1-14 for each digital pin 1 = on 0 = off P = PWM
#// char 15-18 for reading of A0, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading
#// char 19-22 for reading of A1, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading
#// char 23-26 for reading of A2, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading
#// char 27-30 for reading of A3, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading

#// 5) to get the value for a single pin use pinValue(device,pin) to get the value back 1=HIGH, 0= LOW, P=PWM for digital pins and 0-1023 for analog pins

#// remark: the communication between the RPi and Arduino is very sensitive, especially for timings
#// as the RPi is much faster than the Arduino you need to included pauses between commands of atleast 
#// 1 sec to be save, I found that 0.5 seconds works as well (most of the time) but in that case you 
#// occasionally  need to perform a hard reset on the Arduino as it locks up.

#// Created 28 July 2013

#// This example code is in the public domain.

import smbus
import time

# RPi rev 1 = SMBus(0)
# RPi rev 2 = SMBus(1)
bus = smbus.SMBus(1)

# address of the Arduino use "i2cdetect -y 1" from the RPi prompt to detect the Arduinos (up to 127!)
device = 0x21

# initialize variables
pin      = ""  #holds the pin number 0 - 13 or A0 - A3
type     = ""  #holds the pin type: INPUT, OUTPUT, INPUT_PULLUP
mode     = ""  #holds the pinmode: HIGH, LOW, PWM
pwmValue = ""  #holds the pwmValue
pwm      = ""  #holds the pwmValue in 3 digits
val      = ""  #holds a String to be converted into ASCII
cmd      = ""  #holds the first byte of the message for the Arduino
message  = ""  #holds the second - seventh byte of the message for the Arduino
valCmd   = 88                #holds the command as ASCII value 88 = "X" 
valMessage  = [88,88,88,88,88,88] #holds the Message as ASCII values


# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine sends a setPin command to the Arduino to make a pin INPUT, OUTPUT or INPUT_PULLUP
def setPin(device, pin, type):
        cmd = "S"
        message = pinString(pin)+type[0]+"000"
        sendMessage(device, cmd, message)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine sends a writePin command to the Arduino to turn a pin HIGH or LOW
def writePin(device, pin, mode):
        cmd = "W"
        message = pinString(pin)+mode[0]+"000"
        sendMessage(device, cmd, message)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine send an analogWritePin command to the Arduino to set a PWM pin to a duty cycle between 0 and 255
def analogWritePin(device, pin, pwmValue):
        cmd = "A"
        message = pinString(pin)+"X"+pwmString(pwm)
        sendMessage(device, cmd, message)

# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine converts Strings to ASCII code
def StringToBytes(val):
        retVal = []
        for c in val:
                retVal.append(ord(c))
        return retVal


# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine actually transmits the command, 
# sleep is required in order to prevent a request overload on the Arduino
def sendMessage(device, cmd, message):
        cmd=cmd.upper()
        message = message.upper()
        valCmd = ord(cmd)
        valMessage  = StringToBytes(message)
        print("Message: " + cmd + message + " send to device " + str(device))        
        bus.write_i2c_block_data(device, valCmd, valMessage) 
        time.sleep(1)


# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine send a request to the Arduino to provide a 30 byte status update, return all 30 bytes
def getStatus(device):
        status = ""
        for i in range (0, 30):
            status += chr(bus.read_byte(device))
            time.sleep(0.05);
        time.sleep(0.1)        
        return status

# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine send a request to the Arduino to provide a 30 byte status update, return the value of a single pin
def pinValue(device,pin):
        status = ""
        for i in range (0, 30):
            status += chr(bus.read_byte(device))
            time.sleep(0.05);
        pinvalues = {'0':status[0],
                     '1':status[1],
                     '2':status[2],
                     '3':status[3],
                     '4':status[4],
                     '5':status[5],
                     '6':status[6],
                     '7':status[7],
                     '8':status[8],
                     '9':status[9],
                     '10':status[10],
                     '11':status[11],
                     '12':status[12],
                     '13':status[13],
                     'A0':int(status[14]+status[15]+status[16]+status[17])-1000,
                     'A1':int(status[18]+status[19]+status[20]+status[21])-1000,
                     'A2':int(status[22]+status[23]+status[24]+status[25])-1000,
                     'A3':int(status[26]+status[27]+status[28]+status[29])-1000}
        time.sleep(0.1)
        return  pinvalues[pin]


# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine converts a 1 or 2 digit pin into a 2 digit equivalent
def pinString(pin):
        while len(pin) < 2:
              pin = "0"+pin;
        return pin


# ------------------------------------------------------------------------------------------------------------------------------------------------
# this routine converts a 1, 2 or 3 digit pin into a 3 digit equivalent 
def pwmString(pwm):
        while len(pwm) < 3:
              pwm = "0"+pwm;
        return pwm


# ------------------------------------------------------------------------------------------------------------------------------------------------
# this is where the main program starts

while True:

   setPin(33, "13", "Output")  #on Arduino with I2C ID #33 set pin 13 to OUTPUT
   writePin(33,"13", "High")   #on Arduino with I2C ID #33 set pin 13 HIGH
   print ("Status pin 13 =" + pinValue(33,'13'))
   
   writePin(33,"13","Low")     #on Arduino with I2C ID #33 set pin 13 LOW
   print("30 byte status:" + getStatus(33))

