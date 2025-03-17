#include <ESP32Servo.h>

Servo servo1;  // Create servo object 1 (e.g., for pan)
Servo servo2;  // Create servo object 2 (e.g., for tilt)

const int servo1Pin = 19;  // Servo 1 connected to GPIO 18
const int servo2Pin = 18;  // Servo 2 connected to GPIO 19

// User-configurable limits for servo angles (degrees)
int servo1Min = 50;
int servo1Max = 180;
int servo2Min = 80;
int servo2Max = 180;

void setup() {
  Serial.begin(115200);  // Start serial communication at 115200 baud
  
  // Attach servos using the ESP32Servo library
  servo1.attach(servo1Pin);
  servo2.attach(servo2Pin);
}

void loop() {
  // Check if serial data is available
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    int centerX, centerY;
    
    // Expect data in the format: "centerX,centerY"
    if (sscanf(data.c_str(), "%d,%d", &centerX, &centerY) == 2) {
      // Map the received coordinates to the servo angle ranges.
      // Assumes input range of 0-640 for X and 0-480 for Y.
      int pos1 = map(centerX, 0, 640, servo1Max, servo1Min);
      int pos2 = map(centerY, 0, 480, servo2Min, servo2Max);
      
      // Constrain the positions within the user-defined limits
      pos1 = constrain(pos1, servo1Min, servo1Max);
      pos2 = constrain(pos2, servo2Min, servo2Max);
      
      // Update servo positions
      servo1.write(pos1);
      servo2.write(pos2);
    }
  }
  // No additional action if no serial data is received.
  delay(10);  // Small delay to stabilize loop execution
}
