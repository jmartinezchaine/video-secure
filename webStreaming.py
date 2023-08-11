#Import necessary libraries
from flask import Flask, render_template, Response, request
import cv2
import logging
#Initialize the Flask app
app = Flask(__name__)

'''
for ip camera use - rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp' 
for local webcam use cv2.VideoCapture(0)
'''
# list of camera accesses
''' cameras = [
    "rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp",
    "rtsp://username:password@ip_address:554/user=username_password='password'_channel=channel_number_stream=0.sdp",
    ...
]
'''
cameras = [0,1, "http://192.168.1.150:8885/video_feed/0"]
def find_camera(list_id):
    return cameras[int(list_id)]

def gen_frames():
    camera1 = cv2.VideoCapture(0)
    while True:
        success, frame = camera1.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

def gen_multiples_frames(camera_id):
    cam = find_camera(camera_id)  # return the camera access link with credentials. Assume 0?
    # cam = cameras[int(id)]
    cap = cv2.VideoCapture(cam)  # capture the video from the live feed    i+=1

    while True:
        success, frame = cap.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/')
def index():
    return render_template('index_1.html')

#@app.route('/video_feed')
@app.route('/video_feed/<string:list_id>/', methods=["GET"])
def video_feed(list_id):
    logging.info("Request")
    logging.info(request.headers)
    return Response(gen_multiples_frames(list_id), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(port=80, host="0.0.0.0", debug=True)