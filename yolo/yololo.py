import numpy as np
import cv2
import queue
from skimage.metrics import mean_squared_error as ssim
import ultralytics
from ultralytics import YOLO
import torch
from datetime import datetime
import os
from telegram import chat
import time
import atexit

#ultralytics.checks()
print(f"Iniciando YOLO, si el valor es False se utilizará CPU, si es TRUE usara GPU:  ", torch.cuda.is_available())
client = chat.createClient()
yolo_list = ['person', 'cat', 'dog', 'car', 'motorbike', 'bicycle']
yolo_on = True
modelo = 'yolov8n' #nano model
testing = False
thresh = 3000 #Determines the amount of motion required to start recording. Higher values decrease sensitivity to help reduce false positives. Default 350, max 10000."
tail_length = 8 # Number of seconds without motion required to stop recording. Raise this value if recordings are stopping too early. Default 8, max 30.
auto_delete = True
fps = 10
start_frames = 3# entre 1 y 30  Number of consecutive frames with motion required to start recording. Raising this might help if there's too many false positive recordings, especially with a high frame rate stream of 60 FPS. Default 3, max 30.
recording = False
activity_count = 0
yolo_count = 0

chat.mandarMensaje(client, "Iniciando el proceso Yolo: "+modelo+" objetos: " + str(yolo_list), None)

#Set up variables for YOLO detection
if yolo_on:
    stop_error = False

    CONFIDENCE = 0.75
    font_scale = 1
    thickness = 1
    labels = open("coco.names").read().strip().split("\n")
    colors = np.random.randint(0, 255, size=(len(labels), 3), dtype="uint8")
    model = YOLO(modelo+".pt")

    # Check if the user provided list has valid objects
    for coconame in yolo_list:
        if coconame not in labels:
            print("Error! '"+coconame+"' not found in coco.names")
            stop_error = True
    if stop_error:
        exit("Exiting")

def process_yolo(img):
    global label_detected

    results = model.predict(img, conf=CONFIDENCE, verbose=False)[0]
    object_found = False
    # Loop over the detections
    for data in results.boxes.data.tolist():
        # Get the bounding box coordinates, confidence, and class id
        xmin, ymin, xmax, ymax, confidence, class_id = data

        # Converting the coordinates and the class id to integers
        xmin = int(xmin)
        ymin = int(ymin)
        xmax = int(xmax)
        ymax = int(ymax)
        class_id = int(class_id)

        if labels[class_id] in yolo_list:
            object_found = True
            l_idx = yolo_list.index(labels[class_id])
            #label_detected = yolo_list[l_idx]
            label_detected = f"{yolo_list[l_idx]}: {confidence:.2f}"
            print(f"Yolo encontro: " , label_detected )

        # Draw a bounding box rectangle and label on the image
        color = [int(c) for c in colors[class_id]]
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color=color, thickness=thickness)
        text = f"{labels[class_id]}: {confidence:.2f}"
        # Calculate text width & height to draw the transparent boxes as background of the text
        (text_width, text_height) = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, fontScale=font_scale, thickness=thickness)[0]
        text_offset_x = xmin
        text_offset_y = ymin - 5
        box_coords = ((text_offset_x, text_offset_y), (text_offset_x + text_width + 2, text_offset_y - text_height))
        overlay = img.copy()
        cv2.rectangle(overlay, box_coords[0], box_coords[1], color=color, thickness=cv2.FILLED)
        # Add opacity (transparency to the box)
        img = cv2.addWeighted(overlay, 0.6, img, 0.4, 0)
        # Now put the text (label: confidence %)
        cv2.putText(img, text, (xmin, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=font_scale, color=(0, 0, 0), thickness=thickness)
    return img, object_found

q = queue.Queue()
old_frame = 0

# Thread for receiving the stream's frames so they can be processed
def receive_frames(frame):
    global old_frame
    global blank
    global res
    if q.qsize() == 0:
        #Configurar los valores iniciales
        if frame.shape[1]/frame.shape[0] > 1.55:
            res = (256,144)
            #res = (round(img.shape[0]/3),round(img.shape[1]/3))
        else:
            #res = (round(img.shape[0]/3),round(img.shape[1]/3))
            res = (216,162)

        res = (256,144)
        blank = np.zeros((res[1],res[0]), np.uint8)
        resized_frame = cv2.resize(frame, res)
        gray_frame = resized_frame
        old_frame = cv2.GaussianBlur(gray_frame, (5,5), 0)

    q.put(frame)

first = True
# Main loop, en realidad se gestiona desde el socket que esta recibiendo las imagenes
#while loop:
def getImage_with_ia(frame):
    global res
    global old_frame
    global blank
    global activity_count
    global recording
    global yolo_count
    global first
    # primera vez
    overlay = frame
    imagen_path = ''
    if first:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if gray.shape[1]/frame.shape[0] > 1.55:
            res = (256,144)
            #res = (round(img.shape[0]/3),round(img.shape[1]/3))
        else:
            #res = (round(img.shape[0]/3),round(img.shape[1]/3))
            res = (216,162)

        res = (256,144)
        blank = np.zeros((res[1],res[0]), np.uint8)
        resized_frame = cv2.resize(frame, res)
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
        old_frame = cv2.GaussianBlur(gray_frame, (5,5), 0)
        first = False

    q.put(frame)
    if q.empty() != True:
        img = q.get()
        # Resize image, make it grayscale, then blur it
        resized_frame = cv2.resize(img, res)
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
        final_frame = cv2.GaussianBlur(gray_frame, (5,5), 0)

        # Calculate difference between current and previous frame, then get ssim value
        diff = cv2.absdiff(final_frame, old_frame)
        result = cv2.threshold(diff, 5, 255, cv2.THRESH_BINARY)[1]
        ssim_val = int(ssim(result,blank))
        old_frame = final_frame

        # Print value for testing mode
        if testing and ssim_val > thresh:
            print("motion: "+ str(ssim_val))

        # Count the number of frames where the ssim value exceeds the threshold value.
        # If the number of these frames exceeds start_frames value, run YOLO detection.
        # Start recording if an object from the user provided list is detected
        if not recording:
            if ssim_val > thresh:
                activity_count += 1
                if activity_count >= start_frames:
                    if yolo_on:
                        img, object_found = process_yolo(img)
                        if object_found:
                            yolo_count += 1
                        else:
                            yolo_count = 0
                    if not yolo_on or yolo_count > 1:
                        filedate = datetime.now().strftime('%H-%M-%S')
                        if not testing:
                            folderdate = datetime.now().strftime('%Y-%m-%d')
                            if not os.path.isdir(folderdate):
                                os.mkdir(folderdate)
                            filename = '%s/%s.mkv' % (folderdate,filedate)
                            #ffmpeg_thread = threading.Thread(target=start_ffmpeg)
                            #ffmpeg_thread.start()
                            #Guardo la imagen actual
                            imagen_path = '%s/%s.jpg' % (folderdate,filedate)
                            cv2.imwrite(imagen_path,img)
                            telegram_mensaje = filedate + " - Evento detectado: " +  label_detected +" \n Valor de movimiento: "+ str(ssim_val)
                            chat.mandarMensaje(client, telegram_mensaje, imagen_path)
                            print(telegram_mensaje)
                        else:
                            print(filedate + " recording started - Testing mode")
                        recording = True
                        activity_count = 0
                        yolo_count = 0
            else:
                activity_count = 0
                yolo_count = 0

        # If already recording, count the number of frames where there's no motion activity
        # or no object detected and stop recording if it exceeds the tail_length value
        else:
            img, object_found = process_yolo(img)
            if yolo_on and not object_found or not yolo_on and ssim_val < thresh:
                activity_count += 1
                if activity_count >= tail_length:
                    filedate = datetime.now().strftime('%H-%M-%S')
                    if not testing:
                        print(filedate + " recording stopped")
                        os.remove(imagen_path)
                        print(imagen_path + " was auto-deleted")
                    else:
                        print(filedate + " recording stopped - Testing mode")
                    recording = False
                    activity_count = 0
            else:
                activity_count = 0

    else:
        time.sleep(fps/2)
    return img

#Using register() as a decorator
@atexit.register
def goodbye():
    print("GoodBye.")
    chat.mandarMensaje(client, '/Stop', None)
    chat.disconnect(client)
    cv2.destroyAllWindows()