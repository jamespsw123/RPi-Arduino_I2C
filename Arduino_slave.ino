// Arduino I2C Wire Slave version 0.21
// by Racer993 <http://raspberrypi4dummies.wordpress.com/>

// Turns the Arduino to a I2C slave device (for the Raspberry Pi) 
// using the Wire library. Configure pins, read and write to pins
// via a simple instruction set.

// Supported instructions
// pinMode = setPin(device, pinnumber, INPUT/OUTPUT/INPUT_PULLUP)
// digitalWrite = writePin(device,pinnumber,HIGH/LOW)
// analogWrite = analogWritePin(device,pinnumber,0-255)
// getStatus(device)

// A0 - analog read / digital write
// A1 - analog read / digital write
// A2 - analog read / digital write
// A3 - analog read / digital write
// A4 - IN USE as SDA
// A5 - IN USE as SCL

//  1 - digital read / write + RX
//  2 - digital read / write + TX  + Interrupt
//  3 - digital read / write + PWM + Interrupt
//  4 - digital read / write
//  5 - digital read / write + PWM
//  6 - digital read / write + PWM
//  7 - digital read / write
//  8 - digital read / write
//  9 - digital read / write + PWM
// 10 - digital read / write + PWM + SPI - SS
// 11 - digital read / write + PWM + SPI - MOSI
// 12 - digital read / write +       SPI - MISO
// 13 - digital read / write + LED + SPI - SCK

// HOW TO USE

// sending commands

// general: all commands must be 7 bytes long + 1 ending byte

// 1) to set the pinMode write a message with 7 characters on I2C bus to the arduino
// first character = S for set pinMode
// second & third character are pin ID 00 - 13 for digital pins & A0 - A3 for analog pins
// fourth character is to set the mode I for INPUT, O for OUTPUT, P for INPUT_PULLUP
// character 5,6,7 are not used, set to 000

// 2) to turn the pin on or off write a message with 7 characters on I2C bus to the arduino
// first character = W for digitalWrite
// second & third character are pin ID 00 - 13 for digital pins & A0 - A3 for analog pins
// fourth character is to turn off or on H for HIGH and L for LOW
// character 5,6,7 are not used, set to 000

// 3) to turn use PWM write a message with 7 characters on I2C bus to the arduino
// first character = A for analogWrite
// second & third character are pin ID 00 - 13 for digital pins & A0 - A3 for analog pins
// forth character is not used, set to X
// fifth - seventh character are used to write the PWM cycle (000-255)

// 4) to get a status with pin readings send Wire.requestFrom(device, #chars = 30)
// the arduino will send back 30 chars 
// char 1-14 for each digital pin 1 = on 0 = off
// char 15-18 for reading of A0, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading
// char 19-22 for reading of A1, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading
// char 23-26 for reading of A2, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading
// char 27-30 for reading of A3, 1000 is added to the A0 reading in order to guarantee a 4 digit reading, subtract 1000 to get the proper reading

// Created 17 July 2013

// This example code is in the public domain.

#include <Wire.h>

void setup()
{
  int arduinoI2CAddress = 33;     // set the slave address for the Arduino on the I2C buss
    
  Wire.begin(arduinoI2CAddress); // join i2c bus with specified address
  Wire.onRequest(requestEvent);  // register wire.request interrupt event
  Wire.onReceive(receiveEvent);  // register wire.write interrupt event
}

  char sendStatus[31] = "000000000000000000000000000000";  // initialize the container variable
  int index = 0;                                           // initialize the index variable
  char pwm[15] = "00000000000000";                         // initialize the PWM flag container

void loop()
{
  
  String pinStatus="";                                      // initialize pinStatus variable
    
  for(int digitalPin = 0; digitalPin <= 13; digitalPin++)   // loop through 14 digital pins 0 - 13
     {
      if (pwm[digitalPin] == 0)                            // in case PWM is off for the pin, read the pin status
         {
           pinStatus += String (digitalRead(digitalPin));   // read the pin status & add it to the container variable
         }
      else
         { 
           pinStatus += "P";                                // in case PWM is on for the pin, add P to the pin status container string
         } 
     }
  
  for(int analogPin = 0; analogPin <= 3; analogPin++)      // loop through the 4 (unused) analog pins 0 - 3
     {
      pinStatus += String (1000+analogRead(analogPin));    // read the analog value from the pin, add 1000 to make it 4 digit & add it to the container variable
     }  
  
   pinStatus.toCharArray(sendStatus, 31);                  // convert the container variable pinStatus to a char array which can be send over i2c
    
  delay(1000);                                             // wait for an interrupt event
}

//--------------------------------------------------------------------------------
// function that executes whenever a status update is requested by master
// this function is registered as an event, see setup()

void requestEvent() { 
   Wire.write(sendStatus[index]);
    ++index;
    if (index >= 30) {
         index = 0;
    }
 }

//--------------------------------------------------------------------------------
// function that executes whenever a message is received from master
// this function is registered as an event, see setup()

void receiveEvent(int howMany)
{
  int receiveByte = 0;                   // set index to 0
  char command[7];                       // expect 7 char + 1 end byte
  String mode = "";                      // initialize mode variable for holding the mode
  String pin = "";                       // initialize pin variable for holding the pin number as a String
  String awValue = "";                   // intitalize the variable for holding the analogWrite value
  int pinVal;                            // inititalize the variable for holding the pin number as integer
  int awValueVal;                        // initialize the variable for holding the analog write value as integer (only PWM pins!)   
    
  while(Wire.available())                // loop through all incoming bytes
  {
    command[receiveByte] = Wire.read();  // receive byte as a character
    receiveByte++;                       // increase index by 1
  }
  
  pin = String(command[1]) + String(command[2]);                          // combine byte 2 and 3 in order to get the pin number
  awValue = String(command[4]) + String(command[5]) + String(command[6]); // combine byte 5, 6 and 7 in order to get the analogWrite value
  awValueVal = awValue.toInt();                                           // convert the awValue string to a value
  
  if (String(command[1]) != "A" ) { pinVal = pin.toInt();}                // in case of not an analog pin assignment convert into digital pin number
  if (String(command[1]) != "A" ) { pwm[pinVal] = 0;}                     // in case of not an analog pin assignment set PWM flag to 0

// incase of analog pin assignment determine analog pin to be set  
  if (String(command[1]) == "A" && String(command[2]) == "0") { pinVal = A0;}
  if (String(command[1]) == "A" && String(command[2]) == "1") { pinVal = A1;}
  if (String(command[1]) == "A" && String(command[2]) == "2") { pinVal = A2;}
  if (String(command[1]) == "A" && String(command[2]) == "3") { pinVal = A3;}

// if requested set pinmode  
  if (String(command[0]) == "S" && String(command[3]) == "I") { pinMode(pinVal, INPUT);}
  if (String(command[0]) == "S" && String(command[3]) == "O") { pinMode(pinVal, OUTPUT);}
  if (String(command[0]) == "S" && String(command[3]) == "P") { pinMode(pinVal, INPUT_PULLUP);}

// if requested perform digital write
  if (String(command[0]) == "W" && String(command[3]) == "H") { digitalWrite(pinVal, HIGH);}
  if (String(command[0]) == "W" && String(command[3]) == "L") { digitalWrite(pinVal, LOW);}


// if requested perform analog write
  if (String(command[0]) == "A" && pinVal == 3 || pinVal == 5 || pinVal == 6 || pinVal == 9 || pinVal == 10 || pinVal == 11 ) 
      { 
       analogWrite(pinVal, awValueVal);
       pwm[pinVal] = 1;
      }
  
}


