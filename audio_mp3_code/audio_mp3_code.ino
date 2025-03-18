#include <DFRobotDFPlayerMini.h>
#include "HardwareSerial.h"

// Use hardware Serial2 for the DFPlayer module
HardwareSerial mySerial(2);  // ESP32 Serial2 instance
DFRobotDFPlayerMini myDFPlayer;

void setup() {
  Serial.begin(115200);
  Serial.println();
  Serial.println(F("Initializing DFPlayer (MP3-TF-16P)..."));

  // Begin Serial2 on GPIO16 (RX) and GPIO17 (TX) at 9600 baud
  mySerial.begin(9600, SERIAL_8N1, 16, 17);

  // Initialize DFPlayer module
  if (!myDFPlayer.begin(mySerial)) {  
    Serial.println(F("Unable to begin:"));
    Serial.println(F("1. Please recheck the connection!"));
    Serial.println(F("2. Please insert the SD card!"));
    while(true);  // Stay here if initialization fails
  }
  
  Serial.println(F("DFPlayer Mini online."));
  
  // Optional: set volume value from 0 (min) to 30 (max)
  myDFPlayer.volume(20);  
  // Play the first track on the SD card (e.g., 0001.mp3)
  myDFPlayer.play(1);
}

void loop() {
  // Add additional controls or functionality as needed
}
