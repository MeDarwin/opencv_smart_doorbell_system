# Smart Doorbell System with Face Recognition

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-contrib--python-green?logo=opencv&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-red?logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-18+-61DAFB?logo=react&logoColor=black)
![MQTT](https://img.shields.io/badge/MQTT-HiveMQ-FF6B6B?logo=mqtt&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-00758F?logo=mysql&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-Arduino-00979D?logo=arduino&logoColor=white)

A smart doorbell system powered by Raspberry Pi (Backend) and ESP32 (Sensor). It features real-time video streaming, face recognition (auto-training), and activity logging with a React frontend. The system utilizes a local HiveMQ MQTT broker for efficient communication between the sensor and backend.

# Setup Guide

## Prerequisites

- **Python:** 3.8 or newer (3.8–3.11 recommended).  
- **pip:** Python package installer.  
- **Camera:** USB webcam or Raspberry Pi camera accessible to the device running the backend.  
- **MySQL / MariaDB:** A MySQL-compatible database server reachable from the backend.  
- **MQTT broker (HiveMQ):** for sensor messages. The backend expects `MQTT_BROKER` (default: `localhost`).  
- **System libraries (Linux/RPi):** OpenCV may require libs such as `libgl1`, `libglib2.0-0`, etc.

### Python libraries

The backend requires the following Python packages (installed in the backend environment):

- `opencv-contrib-python`
- `numpy`
- `Pillow`
- `Flask`
- `Flask-Cors`
- `mysql-connector-python`
- `paho-mqtt`

Install them using the bundled requirements file:

```bash
cd backend
pip install -r requirements.txt
```

Or install manually:

```bash
pip install opencv-contrib-python numpy Pillow Flask Flask-Cors mysql-connector-python paho-mqtt
```

### Node.js Module

The frontend requires Node.js and npm. Install frontend dependencies:

```bash
cd frontend
npm install
```

All required packages are listed in `frontend/package.json` and will be installed automatically.

## Database Configuration

- Database name: `opencv_smart_doorbell_system`  
- Table name: `riwayat_tamu`

### Database setup example

Run this SQL (adjust types/names as needed):

```sql
CREATE DATABASE IF NOT EXISTS opencv_smart_doorbell_system;
USE opencv_smart_doorbell_system;

CREATE TABLE IF NOT EXISTS riwayat_tamu (
  id INT AUTO_INCREMENT PRIMARY KEY,
  waktu DATETIME,
  nama VARCHAR(255),
  status VARCHAR(255),
  file_foto VARCHAR(255)
);
```

### Other notes

- Ensure `DB_CONFIG` in backend Python files matches your DB credentials and host.  
- If using MQTT, ensure the broker is running and `MQTT_BROKER` in your backend file points to it.  
- Confirm camera device index (0 or 1) in `backend/ambil_data.py` / `backend/main.py` if multiple cameras are attached.


## Establishing Connection (Configuration)

Ensure IP addresses match your network. Example assumption:
- Raspberry Pi (running HiveMQ & Backend): `192.168.137.200`

### A. ESP32 Configuration (Arduino IDE)  
The ESP32 connects to the HiveMQ broker running on the Pi. Edit your `.ino`:

```cpp
// Example: set broker and topic (assuming mqtt runs on port 1883)
const char* mqtt_server = "MQTT_BROKER_ADDRESS"; // E.g: broker.hivemq.com
const char* mqtt_topic = "doorbell/sensor/depan";

void setup() {
    // ...
    // Default mqtt port is 1883
    client.setServer(mqtt_server, 1883); // <- Change port if the mqtt connection is modified
    // ...
}
```

### B. Backend Configuration (main.py)
Since the backend runs on the same machine as HiveMQ, use localhost. Edit `main.py`:

```python
# MQTT Config
MQTT_BROKER = "localhost"  # Points to local HiveMQ instance
MQTT_TOPIC = "doorbell/sensor/depan"
```

### C. Frontend Configuration (src/App.jsx)  
The React app consumes the backend API. Edit `src/App.jsx`:

```javascript
// Point this to your Raspberry Pi's IP Address and backend port
const API_URL = "http://192.168.137.200:5000";
```

## Running the System

1. Start HiveMQ (ensure the broker is active).  
2. Start Backend:
```bash
python main.py
```
Wait for backend initialization messages (e.g. "[INIT] SUKSES! ... ID Wajah dipelajari.").  
3. Start Frontend:
```bash
npm run dev
```
4. Power on ESP32 and verify it connects to Wi‑Fi and sends data to HiveMQ.

## Troubleshooting & Tips

- If backend and HiveMQ are on the same Pi, keep `MQTT_BROKER = "localhost"`. If broker is remote, use its local IP.  
- For frontends running in a browser, consume the backend API (SSE, WS, or HTTP endpoints) rather than raw MQTT unless the broker exposes WebSocket support.  
- Use JSON payloads and consistent topic naming (e.g. `doorbell/sensor/depan`).