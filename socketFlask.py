import base64
import os
import queue
import asyncio
import cv2
import numpy as np
from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
from yolo import yololo
import logging

logging.getLogger('socketio').setLevel(logging.ERROR)
logging.getLogger('engineio').setLevel(logging.ERROR)

app = Flask(__name__)
app.config["SECRET_KEY"] = "esto_es_un_secreto"
socketio = SocketIO(app)

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


def base64_to_image(base64_string):
    # Extract the base64 encoded binary data from the input string
    base64_data = base64_string.split(",")[1]
    # Decode the base64 data to bytes
    image_bytes = base64.b64decode(base64_data)
    # Convert the bytes to numpy array
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    # Decode the numpy array as an image using OpenCV
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    return image


@socketio.on("connect")
def test_connect():
    print("Connected")
    emit("my response", {"data": "Connected"})


@socketio.on("image")
def receive_image(image):
    # Decode the base64-encoded image data
    image = base64_to_image(image)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    frame_resized = cv2.resize(gray, (400, 300))

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]

    result, frame_encoded = cv2.imencode(".jpg", frame_resized, encode_param)

    processed_img_data = base64.b64encode(frame_encoded).decode()

    b64_src = "data:image/jpg;base64,"
    processed_img_data = b64_src + processed_img_data

    emit("processed_image", processed_img_data)
    #receive_image_ia(image)

@socketio.on("image_ia")
def receive_image_ia(imagen):
    # Decode the base64-encoded image data
    image_2 = base64_to_image(imagen)

    gray = cv2.cvtColor(image_2, cv2.COLOR_BGR2GRAY)

    frame_resized = cv2.resize(gray, (400, 300))

    # esto habria que ver que onda, si se peude usar un thread a parte para encolar y que el proceso se realice en otro
    #yololo.receive_frames(frame_resized)
    gray_with_ai = yololo.getImage_with_ia(image_2)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 40]

    if not gray_with_ai.any():
        blank = np.zeros((400,300), np.uint8)
        results = blank

    result, frame_encoded = cv2.imencode(".jpg", gray_with_ai, encode_param)

    processed_img_data = base64.b64encode(frame_encoded).decode()

    b64_src = "data:image/jpg;base64,"
    processed_img_data = b64_src + processed_img_data


    emit("processed_image_ia", processed_img_data)

@app.route("/")
def index():
    return render_template("flasksocket.html")

if __name__ == "__main__":
    socketio.run(app, debug=False, port=5000, host='0.0.0.0', allow_unsafe_werkzeug=True, keyfile='key.pem', certfile='cert.pem')