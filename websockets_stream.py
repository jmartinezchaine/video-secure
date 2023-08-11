import logging

import tornado.httpserver
import tornado.websocket
import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.gen
import threading
import asyncio
import socket
import numpy as np
import imutils
import copy
import time
import cv2
import os
from base64 import b64encode
from tornado.options import define, options

bytes = b''

lock = threading.Lock()
connectedDevices = set()


class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super(WSHandler, self).__init__(*args, **kwargs)
        self.outputFrame = None
        self.frame = None
        self.id = None
        self.executor = tornado.concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.stopEvent = threading.Event()

    def process_frames(self):
        if self.frame is None:
            return
        frame = imutils.rotate_bound(self.frame.copy(), 90)
        (flag, encodedImage) = cv2.imencode(".jpg", frame)

        # ensure the frame was successfully encoded
        if not flag:
            return
        self.outputFrame = encodedImage.tobytes()

    def open(self):
        print('new connection')
        connectedDevices.add(self)
        #self.t = threading.Thread(target=self.process_frames)
        #self.t.daemon = True
        #self.t.start()

    def on_message(self, message):
        if self.id is None:
            self.id = message
        else:
            self.frame = cv2.imdecode(np.frombuffer(
                message, dtype=np.uint8), cv2.IMREAD_COLOR)
            self.process_frames()
            tornado.ioloop.IOLoop.current().run_in_executor(self.executor, self.process_frames)

    def on_close(self):
        print('connection closed')
        self.stopEvent.set()
        connectedDevices.remove(self)

    def check_origin(self, origin):
        return True

import base64

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


class StreamHandler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self, slug):
        self.set_header(
            'Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.set_header('Pragma', 'no-cache')
        self.set_header(
            'Content-Type', 'multipart/x-mixed-replace;boundary=--jpgboundary')
        self.set_header('Connection', 'close')

        my_boundary = "--jpgboundary"
        client = None
        for c in connectedDevices:
            if c.id == slug:
                print(slug)
                client = c
                break
        while client is not None:
            jpgData = client.outputFrame
            if jpgData is None:
                print("empty frame")
                continue
            self.write(my_boundary)
            self.write("Content-type: image/jpeg\r\n")
            self.write("Content-length: %s\r\n\r\n" % len(jpgData))
            self.write(jpgData)
            self.flush()
            #yield tornado.gen.Task(self.flush)

from PIL import Image
import io
class ImageHandler(tornado.web.RequestHandler):
    def get(self, filename):
        f = Image.open('static/images/fulls/' + filename)
        o = io.BytesIO()
        f.save(o, format="JPEG")
        s = o.getvalue()
        self.set_header('Content-type', 'image/jpg')
        self.set_header('Content-length', len(s))
        self.write(s)

class TemplateHandler(tornado.web.RequestHandler):
    def get(self):
        deviceIds = [d.id for d in connectedDevices]
        self.render("index.html", url="http://192.168.1.150:8885/video_feed/", deviceIds=deviceIds, photo="static/images/fulls/10.jpg")

define('port', default=8885, help='Listening port', type=int)
class Application(tornado.web.Application):
    def __init__(self):
        handlers= [(r'/video_feed/([^/]+)', StreamHandler),
                   (r'/ws', WSHandler),
                   (r'/', TemplateHandler),
                   (r'/img/(?P<filename>.+\.jpg)?', ImageHandler),]

        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
            cookie_secret=b64encode(os.urandom(64)),
            debug=True,
            auto_reload=True,
            websocket_ping_interval=10,
            websocket_ping_timeout=30,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Configure logging
        options.log_file_max_size = (1024**2)*10
        logging.getLogger().setLevel(logging.INFO)
        tornado.log.enable_pretty_logging()

        print("Listening on port: %d" % options.port)


'''application = tornado.web.Application(
    [(r'/video_feed/([^/]+)', StreamHandler),
     (r'/ws', WSHandler),
     (r'/', TemplateHandler)],
    websocket_ping_interval=10,
    websocket_ping_timeout=30,)'''


if __name__ == "__main__":

    '''http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8885)
    myIP = socket.gethostbyname(socket.gethostname())
    print('*** Websocket Server Started at %s ***' % myIP)
    tornado.ioloop.IOLoop.current().start()'''
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
