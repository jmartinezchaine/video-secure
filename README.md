# Real-time Object Tracking with YOLOv8

**socketFlask**

- Servidor de webSocket (Flask + flask_socketio)
- Utiliza Yolo para reconocimiento de objetos
- Es configurable para una lista de objetos
- Se integra con Telegram para enviar el Evento 

Mediante página con Js se lee la camara y se la transmite mediante websocket a Flask,
este procesa la imagen y se la envia a Yolo para su reconocimiento, 
cuando éste detecta un Evento se envia por telegram.



Se utilizan repositorios de ejemplos, entre ellos

- Phazer Tech


**websockets_stream**
Servidor con Tornado y websokets

No lo gre aun integrar el stream con Yolo, tengo problemas de conversion de datos que 
desconozco por ahora.


**webstreaming**

Servidor Flask que lee la camara por http
