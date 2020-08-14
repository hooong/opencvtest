from flask import Response
from flask import Flask
from flask import render_template
import threading
import argparse
import datetime
import time
import cv2
import numpy as np

outputFrame = None
lock = threading.Lock()

# flask init
app = Flask(__name__)

# 카메라 영상 캡쳐
vs = cv2.VideoCapture(0)
time.sleep(2.0)

# index 요청
@app.route("/")
def index():
	return render_template("index.html")

# frame 얻어오는 함수
def getvideo():
	global vs, outputFrame, lock

	while True:
		ret, frame = vs.read()
		gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

		with lock:
			# frame별 저장 
			outputFrame = frame

def generate():
	global outputFrame, lock

	while True:
		with lock:
			if outputFrame is None:
				continue

			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

			if not flag:
				continue

		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

# 이미지 전송
@app.route("/video_feed")
def video_feed():
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':

	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, required=True,
		help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, required=True,
		help="ephemeral port number of the server (1024 to 65535)")
	args = vars(ap.parse_args())

	# 이미지 불러오는 쓰레드 시작
	t = threading.Thread(target=getvideo)
	t.daemon = True
	t.start()

	# 플라스크 app 시작
	app.run(host=args["ip"], port=args["port"], debug=True,
		threaded=True, use_reloader=False)

# 카메라 릴리즈
vs.release()