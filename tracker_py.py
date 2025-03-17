import serial
import time
import cv2
import numpy as np
from ultralytics import YOLO

# Configuration settings (update these as needed)
SERIAL_PORT = "COM3"                # Change as required (e.g., '/dev/ttyUSB0' for Linux)
BAUD_RATE = 115200
CAMERA_INDEX = 1                    # Camera index (0, 1, etc.)
MODEL_PATH = r"C:\Users\coder\Desktop\bird_detection\my_model\my_model.pt"
CONF_THRESH = 0.8                   # Confidence threshold for detection

def init_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Serial connected on {port} at {baud} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
        exit(1)

def main():
    # Initialize serial communication with ESP32
    ser = init_serial(SERIAL_PORT, BAUD_RATE)
    
    # Load the YOLO model for detection
    model = YOLO(MODEL_PATH)
    
    # Open the camera
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit(1)
    
    print("Starting bird tracking. Press 'q' to exit.")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame from camera.")
                break

            # Run YOLO detection on the current frame
            results = model(frame, verbose=False)
            detections = results[0].boxes

            valid_detection = None
            # Process detections and filter based on the confidence threshold
            for detection in detections:
                conf = detection.conf.item()
                if conf >= CONF_THRESH:
                    valid_detection = detection
                    break  # Process only the first valid detection per frame

            if valid_detection is not None:
                xyxy = valid_detection.xyxy.cpu().numpy().squeeze()
                # Ensure the bounding box data is valid
                if xyxy.ndim == 0 or len(xyxy) < 4:
                    continue
                
                xmin, ymin, xmax, ymax = xyxy.astype(int)
                centerX = (xmin + xmax) // 2
                centerY = (ymin + ymax) // 2

                # Create the data string to send via UART
                data_str = f"{centerX},{centerY}\n"
                try:
                    ser.write(data_str.encode())
                except serial.SerialException as e:
                    print(f"Serial write error: {e}")
                    break

                # Draw bounding box and center point on the frame
                cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                cv2.circle(frame, (centerX, centerY), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"{centerX},{centerY}", (xmin, ymin - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            # Display the processed frame
            cv2.imshow("Bird Tracking", frame)

            # Exit if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Optional: small delay to control frame processing rate
            time.sleep(0.02)
    except KeyboardInterrupt:
        print("User interrupted the process.")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        ser.close()
        print("Resources released. Exiting.")

if __name__ == '__main__':
    main()
