import serial
import time
import cv2
import numpy as np
import base64
import requests
import json
import re
from ultralytics import YOLO

# --- Configuration ---
SERIAL_PORT = "/dev/ttyUSB0"  # Update for your Fedora environment if needed
BAUD_RATE = 115200
CAMERA_INDEX = 1
MODEL_PATH = r"/home/steve/Desktop/bird/my_model.pt"
CONF_THRESH = 0.8

# Ollama Settings
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3"  # Ensure you have pulled the vision-capable Gemma 3 tag
VERIFICATION_COOLDOWN = 3.0  # How long to trust a "Safe" reading before re-verifying (seconds)

def init_serial(port, baud):
    try:
        ser = serial.Serial(port, baud, timeout=1)
        print(f"Serial connected on {port} at {baud} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Error opening serial port {port}: {e}")
        exit(1)

def verify_with_gemma(frame, xmin, ymin, xmax, ymax):
    """Crops the target, sends it to Ollama, and returns True if safe to fire."""
    # Add a little padding to the crop for context
    h, w = frame.shape[:2]
    pad = 30
    c_ymin, c_ymax = max(0, ymin - pad), min(h, ymax + pad)
    c_xmin, c_xmax = max(0, xmin - pad), min(w, xmax + pad)
    
    crop = frame[c_ymin:c_ymax, c_xmin:c_xmax]
    _, buffer = cv2.imencode('.jpg', crop)
    img_str = base64.b64encode(buffer).decode('utf-8')

    prompt = (
        "Analyze this image. Is it exclusively a bird? Are there any humans, dogs, or other pets visible? "
        "Respond ONLY with a JSON object in this format: {\"safe_to_fire\": true} or {\"safe_to_fire\": false}"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "images": [img_str]
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=5)
        response_data = response.json()
        response_text = response_data.get("response", "").strip()
        
        # Extract JSON from the markdown block if Gemma formats it that way
        json_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(0))
            return result.get("safe_to_fire", False)
        return False
    except Exception as e:
        print(f"GenAI Verification Error: {e}")
        return False # Fail safe: default to off

def main():
    ser = init_serial(SERIAL_PORT, BAUD_RATE)
    model = YOLO(MODEL_PATH)
    cap = cv2.VideoCapture(CAMERA_INDEX)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        exit(1)
        
    print("Starting AI bird tracking. Press 'q' to exit.")
    
    is_safe_to_fire = False
    last_verification_time = 0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            results = model(frame, verbose=False)
            valid_detection = None
            
            for detection in results[0].boxes:
                if detection.conf.item() >= CONF_THRESH:
                    valid_detection = detection
                    break 

            # Default laser state to 0 (off)
            laser_state = 0 
            centerX, centerY = 320, 240 # Default center to avoid wild swings

            if valid_detection is not None:
                xyxy = valid_detection.xyxy.cpu().numpy().squeeze()
                if xyxy.ndim > 0 and len(xyxy) == 4:
                    xmin, ymin, xmax, ymax = xyxy.astype(int)
                    centerX = (xmin + xmax) // 2
                    centerY = (ymin + ymax) // 2

                    # Draw YOLO box
                    cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (255, 0, 0), 2)

                    # --- GenAI Verification Logic ---
                    current_time = time.time()
                    if current_time - last_verification_time > VERIFICATION_COOLDOWN:
                        print("Verifying target with Gemma 3...")
                        is_safe_to_fire = verify_with_gemma(frame, xmin, ymin, xmax, ymax)
                        last_verification_time = current_time
                        print(f"Verification Result: {'SAFE' if is_safe_to_fire else 'UNSAFE'}")

                    if is_safe_to_fire:
                        laser_state = 1
                        cv2.circle(frame, (centerX, centerY), 8, (0, 0, 255), -1)
                        cv2.putText(frame, "LASER ARMED", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    else:
                        cv2.circle(frame, (centerX, centerY), 8, (0, 255, 255), -1)
                        cv2.putText(frame, "TRACKING (SAFE MODE)", (xmin, ymin - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            else:
                # No bird detected, reset safety state immediately
                is_safe_to_fire = False

            # Send data to ESP32 format: "X,Y,LaserState\n"
            data_str = f"{centerX},{centerY},{laser_state}\n"
            try:
                ser.write(data_str.encode())
            except serial.SerialException:
                break

            cv2.imshow("GenAI Bird Deterrent", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        # Send one last command to turn the laser off before exiting
        try:
            ser.write(b"320,240,0\n")
        except:
            pass
        cap.release()
        cv2.destroyAllWindows()
        ser.close()
        print("Exited cleanly.")

if __name__ == '__main__':
    main()