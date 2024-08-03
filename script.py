from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import mediapipe as mp
import base64
import numpy as np
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.5)
mp_drawing = mp.solutions.drawing_utils

# Create a ThreadPoolExecutor to handle image processing in separate threads
executor = ThreadPoolExecutor(max_workers=2)

def is_victory_sign(hand_landmarks):
    index_finger_tip = hand_landmarks.landmark[8]
    middle_finger_tip = hand_landmarks.landmark[12]
    index_finger_mcp = hand_landmarks.landmark[5]
    middle_finger_mcp = hand_landmarks.landmark[9]
    is_index_finger_up = index_finger_tip.y < index_finger_mcp.y
    is_middle_finger_up = middle_finger_tip.y < middle_finger_mcp.y
    return is_index_finger_up and is_middle_finger_up

def is_index_finger_up(hand_landmarks):
    index_finger_tip = hand_landmarks.landmark[8]
    index_finger_mcp = hand_landmarks.landmark[5]
    is_index_finger_up = index_finger_tip.y < index_finger_mcp.y
    is_other_fingers_down = all(
        hand_landmarks.landmark[i].y > hand_landmarks.landmark[i - 3].y
        for i in [12, 16, 20]
    )
    return is_index_finger_up and is_other_fingers_down

def is_thumb_left(hand_landmarks):
    thumb_tip = hand_landmarks.landmark[4]
    thumb_mcp = hand_landmarks.landmark[2]
    is_thumb_left = thumb_tip.x < thumb_mcp.x
    return is_thumb_left

def is_pinky_up(hand_landmarks):
    pinky_tip = hand_landmarks.landmark[20]
    pinky_mcp = hand_landmarks.landmark[17]
    is_pinky_up = pinky_tip.y < pinky_mcp.y
    return is_pinky_up

def is_all_fingers_open(hand_landmarks):
    return all(
        hand_landmarks.landmark[i].y < hand_landmarks.landmark[i - 3].y
        for i in [8, 12, 16, 20]
    )

def process_image(image):
    # Flip the image horizontally
    flipped_image = cv2.flip(image, 1)
    rgb_image = cv2.cvtColor(flipped_image, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_image)
    
    if results.multi_hand_landmarks:
        for i, hand_landmarks in enumerate(results.multi_hand_landmarks):
            handedness = results.multi_handedness[i].classification[0].label
            
            # Only process if the hand is the right hand
            if handedness == 'Right':
                response = {
                    "handedness": handedness,
                    "is_all_fingers_open": is_all_fingers_open(hand_landmarks),
                    "is_victory_sign": is_victory_sign(hand_landmarks),
                    "is_index_finger_up": is_index_finger_up(hand_landmarks),
                    "is_thumb_left": is_thumb_left(hand_landmarks),
                    "is_pinky_up": is_pinky_up(hand_landmarks)
                }
                return response
        
        return {"error": "Right hand not detected"}  # No right hand detected
    else:
        return {"error": "No hand detected"}

@socketio.on('image')
def handle_image(data):
    image_data = data.split(",")[1]
    nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Process image in a separate thread
    future = executor.submit(process_image, image)
    response = future.result()
    
    emit('result', response)

if __name__ == '__main__':
    socketio.run(app, debug=True)
