from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app) # Wajib, biar React di Laptop boleh ambil data dari Raspi

# --- KONFIGURASI DB ---
# Sesuaikan password database kamu
DB_CONFIG = {
    'host': '192.168.137.200',
    'user': 'phpmyadmin',
    'password': 'pi-2', 
    'database': 'opencv_smart_doorbell_system'
}

# Lokasi Folder Foto (Sesuaikan nama foldernya jika beda)
FOTO_FOLDER = os.path.join(os.getcwd(), "static/foto_tamu")

# 1. API UNTUK KIRIM DATA JSON (YANG DITANYAKAN TADI)
@app.route('/api/data')
def get_data():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        # PENTING: dictionary=True bikin outputnya jadi JSON {key: value}
        # Bukan cuma urutan angka (tuple)
        cursor = conn.cursor(dictionary=True) 
        
        # Ambil 10 data terakhir, urut dari yang paling baru
        cursor.execute("SELECT * FROM riwayat_tamu ORDER BY waktu DESC LIMIT 10")
        data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 2. API UNTUK BUKA FOTO
@app.route('/foto/<path:filename>')
def serve_foto(filename):
    return send_from_directory(FOTO_FOLDER, filename)

if __name__ == '__main__':
    # host='0.0.0.0' artinya bisa diakses dari luar (laptop)
    app.run(host='0.0.0.0', port=5000, debug=True)