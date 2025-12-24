import cv2
import numpy as np
import os
import time
import threading
import datetime
import mysql.connector
import paho.mqtt.client as mqtt
from flask import Flask, Response, jsonify, send_from_directory, request # Tambah request
from flask_cors import CORS
from PIL import Image

# ==========================================
# KONFIGURASI
# ==========================================
MQTT_BROKER = "localhost" 
MQTT_TOPIC = "doorbell/sensor/depan"

DB_CONFIG = {
    'host': 'localhost',
    'user': 'phpmyadmin',
    'password': 'pi-2',
    'database': 'opencv_smart_doorbell_system'
}

FOTO_FOLDER = os.path.join(os.getcwd(), "static/foto_tamu")
DATASET_PATH = 'dataset'
names = ['None', 'Alfred', 'Darwin', 'Tamu 1', 'Tamu VIP'] 

# ==========================================
# GLOBAL VARIABLES
# ==========================================
outputFrame = None
lock = threading.Lock()

sensor_trigger_aktif = False 
last_trigger_time = 0
WAKTU_TIMEOUT_SENSOR = 10 

# GANTI VARIABLE INI:
last_heartbeat_time = 0  # Waktu terakhir browser ngirim sinyal

app = Flask(__name__)
CORS(app)

# ==========================================
# FUNGSI TRAINING & MQTT (SAMA SEPERTI SEBELUMNYA)
# ==========================================
# (Langsung copy paste fungsi getImagesAndLabels, on_connect, on_message, start_mqtt dari kode sebelumnya)
# Saya singkat disini biar gak kepanjangan, isinya SAMA PERSIS.
def getImagesAndLabels(path):
    if not os.path.exists(path): return [], []
    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
    faceSamples=[]; ids = []
    temp_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    for imagePath in imagePaths:
        try:
            if os.path.split(imagePath)[-1] == ".DS_Store": continue
            PIL_img = Image.open(imagePath).convert('L'); img_numpy = np.array(PIL_img,'uint8')
            id = int(os.path.split(imagePath)[-1].split(".")[1])
            faces = temp_detector.detectMultiScale(img_numpy)
            for (x,y,w,h) in faces: faceSamples.append(img_numpy[y:y+h,x:x+w]); ids.append(id)
        except: continue
    return faceSamples, ids

def on_connect(client, userdata, flags, rc, properties):
    print(f"[MQTT] Konek Localhost! Subs: {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    global last_trigger_time, sensor_trigger_aktif
    pesan = msg.payload.decode()
    if pesan == "ADA_ORANG":
        last_trigger_time = time.time()
        if not sensor_trigger_aktif:
            print(">>> [SENSOR] ADA ORANG! Mengaktifkan Kamera...")
            sensor_trigger_aktif = True

def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect; client.on_message = on_message
    try: client.connect(MQTT_BROKER, 1883, 60); client.loop_forever()
    except Exception as e: print(f"[MQTT ERROR] {e}")

# ==========================================
# CAMERA ENGINE (LOGIKA HEARTBEAT)
# ==========================================
def start_camera_loop():
    global outputFrame, sensor_trigger_aktif, last_trigger_time, last_heartbeat_time
    
    # Init Training (Sama)
    print("\n[INIT] Sedang mentraining wajah...")
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    faceCascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    model_ready = False
    try:
        faces, ids = getImagesAndLabels(DATASET_PATH)
        if len(faces) > 0: recognizer.train(faces, np.array(ids)); model_ready = True; print("[INIT] SUKSES!")
        else: print("[WARNING] Dataset kosong.")
    except: pass

    cam = None
    last_save_time = 0 
    INTERVAL_SIMPAN = 5.0 
    WARMUP_FRAMES = 30  
    frames_read = 0     

    print("[SYSTEM] SIAP MEMANTAU...\n")

    while True:
        # LOGIKA BARU: Cek Heartbeat
        # Jika sekarang - heartbeat terakhir < 5 detik, berarti ada penonton
        ada_penonton = (time.time() - last_heartbeat_time) < 5.0

        kamera_harus_nyala = sensor_trigger_aktif or ada_penonton

        if kamera_harus_nyala:
            if cam is None:
                # Debugging biar jelas penyebab nyala
                penyebab = []
                if sensor_trigger_aktif: penyebab.append("SENSOR")
                if ada_penonton: penyebab.append("VIEWER")
                
                print(f"[CAM] STARTING... (Penyebab: {', '.join(penyebab)})")
                cam = cv2.VideoCapture(0)
                cam.set(3, 640)
                cam.set(4, 480)
                frames_read = 0 
                time.sleep(0.2)
            
            ret, img = cam.read()
            if ret:
                frames_read += 1 
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = faceCascade.detectMultiScale(gray, 1.2, 5)
                nama_terdeteksi = "Unknown" 

                # Logic Recognition (Sama)
                for (x, y, w, h) in faces:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    if model_ready:
                        try:
                            id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
                            if (confidence < 55): nama_terdeteksi = names[id]; conf_text = f"{round(100 - confidence)}%"
                            else: nama_terdeteksi = "Unknown"; conf_text = f"{round(100 - confidence)}%"
                            cv2.putText(img, str(nama_terdeteksi), (x+5,y-5), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                        except: pass
                    else:
                        cv2.putText(img, "TARGET", (x,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

                # Indikator Visual (Update Teks Viewer)
                if sensor_trigger_aktif:
                    if frames_read < WARMUP_FRAMES:
                        cv2.putText(img, "ADJUSTING LIGHT...", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
                    else:
                        cv2.circle(img, (600, 40), 10, (0, 0, 255), -1) 
                        cv2.putText(img, "REC", (540, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)


                with lock: outputFrame = img.copy()

                # Simpan DB (Sama)
                sekarang = time.time()
                if sensor_trigger_aktif and (frames_read > WARMUP_FRAMES) and (sekarang - last_save_time > INTERVAL_SIMPAN):
                    try:
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"tamu_{timestamp}.jpg"
                        if not os.path.exists(FOTO_FOLDER): os.makedirs(FOTO_FOLDER)
                        path_full = os.path.join(FOTO_FOLDER, filename)
                        cv2.imwrite(path_full, img)
                        
                        status_db = "Peringatan"; nama_db = "Gerakan Mencurigakan"
                        if len(faces) > 0:
                            if nama_terdeteksi != "Unknown": status_db = "Aman (Dikenali)"; nama_db = nama_terdeteksi
                            else: status_db = "Peringatan (Asing)"; nama_db = "Orang Asing"
                        
                        conn = mysql.connector.connect(**DB_CONFIG); cursor = conn.cursor()
                        sql = "INSERT INTO riwayat_tamu (waktu, nama, status, file_foto) VALUES (%s, %s, %s, %s)"
                        val = (datetime.datetime.now(), nama_db, status_db, filename)
                        cursor.execute(sql, val); conn.commit(); conn.close()
                        last_save_time = sekarang; print(f"[FOTO] Cekrek! {nama_db}")
                    except Exception as e: print(f"[ERROR SIMPAN] {e}")

            # Timeout Sensor (Sama)
            if sensor_trigger_aktif and (time.time() - last_trigger_time > WAKTU_TIMEOUT_SENSOR):
                print("[SENSOR] Timeout. Stop Mode Rekam.")
                sensor_trigger_aktif = False

        else:
            if cam is not None:
                print("[CAM] OFF (Standby - Tidak ada Viewer/Sensor)")
                cam.release(); cam = None
            blank = np.zeros((480,640,3), np.uint8)
            cv2.putText(blank, "SYSTEM SLEEP", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (100, 100, 100), 2)
            with lock: outputFrame = blank.copy()
            time.sleep(0.5)

# ==========================================
# FLASK SERVER (TAMBAH ROUTE HEARTBEAT)
# ==========================================
@app.route('/api/heartbeat', methods=['POST'])
def heartbeat():
    global last_heartbeat_time
    # Update waktu terakhir sinyal diterima
    last_heartbeat_time = time.time()
    return jsonify({"status": "alive"})

# Generate Video (Sederhana, gak perlu counter lagi)
def generate():
    global outputFrame, lock
    while True:
        with lock:
            if outputFrame is None: continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            if not flag: continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')
        time.sleep(0.04) 

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/api/data')
def get_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG); cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM riwayat_tamu ORDER BY waktu DESC LIMIT 10")
        data = cursor.fetchall(); conn.close()
        return jsonify(data)
    except: return jsonify([])

@app.route('/foto/<path:filename>')
def serve_foto(filename): return send_from_directory(FOTO_FOLDER, filename)

if __name__ == '__main__':
    t_mqtt = threading.Thread(target=start_mqtt); t_mqtt.daemon = True; t_mqtt.start()
    t_cv = threading.Thread(target=start_camera_loop); t_cv.daemon = True; t_cv.start()
    print("=== SMART DOORBELL ===")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)