#include <ESP32Servo.h>

Servo myServo;
int servoPin = 19;  // Use any PWM-capable GPIO pin
int angle = 90;  // Default angle

void setup() {
    Serial.begin(115200);  // Start serial communication
    myServo.attach(servoPin);
    myServo.write(angle);  // Set initial position
    Serial.println("Enter an angle between 0 and 180:");
}

void loop() {
    if (Serial.available() > 0) {  // Check if data is available
        int newAngle = Serial.parseInt();  // Read the integer input
        if (newAngle >= 0 && newAngle <= 180) {
            angle = newAngle;  // Update the stored angle
            myServo.write(angle);  // Move servo
            Serial.print("Servo moved to: ");
            Serial.println(angle);
        } else {
            Serial.println("Invalid angle! Enter a value between 0 and 180.");
        }
        
        // Clear the serial buffer to avoid unwanted behavior
        while (Serial.available()) Serial.read();
    }
}
