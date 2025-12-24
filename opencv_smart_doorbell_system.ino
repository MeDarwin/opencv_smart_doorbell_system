#include <WiFi.h>
#include <PubSubClient.h>

// --- KONFIGURASI WIFI & MQTT ---
const char* ssid = "YOUR WIFI SSID";
const char* password = "YOUR WIFI PASSWORD";
const char* mqtt_server = "MQTT_BROKER_ADDRESS"; // E.g: broker.hivemq.com
const char* mqtt_topic = "doorbell/sensor/depan";

WiFiClient espClient;
PubSubClient client(espClient);

// --- PIN HC-SR04 (ESP32) ---
const int trigPin = 5;   
const int echoPin = 18;  

// Variabel
long duration;
int distance;
bool orangTerdeteksi = false;

// --- FUNGSI LOGGING (BIAR CANTIK) ---
void log(String tag, String pesan) {
  // Format: [TAG]    Pesan
  Serial.printf("[%-8s] %s\n", tag.c_str(), pesan.c_str());
}

void setup() {
  Serial.begin(115200);
  
  // Setup Pin
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);

  // --- STARTUP BANNER ---
  Serial.println("\n\n");
  Serial.println("=============================================");
  Serial.println("   SMART DOORBELL SYSTEM - SENSOR NODE (ESP32)");
  Serial.println("=============================================");
  
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  
  log("SYSTEM", "Inisialisasi selesai. Memulai loop sensor...");
  Serial.println("---------------------------------------------");
}

void setup_wifi() {
  delay(10);
  String msg = "Menghubungkan ke " + String(ssid) + "...";
  log("WIFI", msg);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(""); // Baris baru setelah titik-titik

  log("WIFI", "Terhubung!");
  log("WIFI", "IP Address: " + WiFi.localIP().toString());
}

void reconnect() {
  while (!client.connected()) {
    log("MQTT", "Mencoba koneksi ke Broker...");
    
    String clientId = "ESP32-Doorbell-" + String(random(0xffff), HEX);

    if (client.connect(clientId.c_str())) {
      log("MQTT", "Terhubung ke HiveMQ!");
      log("MQTT", "Client ID: " + clientId);
    } else {
      String failMsg = "Gagal (rc=" + String(client.state()) + "). Coba lagi 5 detik...";
      log("MQTT", failMsg);
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // --- BACA SENSOR JARAK ---
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = duration * 0.034 / 2;

  // --- LOGIKA UTAMA & LOGGING ---
  
  // 1. Kondisi Ada Orang (< 20cm)
  if (distance > 0 && distance < 20) {
    
    // Kirim pesan KEEP-ALIVE ke MQTT
    client.publish(mqtt_topic, "ADA_ORANG"); 
    
    // Tampilkan log (Gunakan warna merah/capslock visual lewat teks)
    String logMsg = "OBJEK TERDETEKSI (" + String(distance) + " cm) -> KIRIM SINYAL";
    log("TRIGGER", logMsg);
    
    orangTerdeteksi = true; 
    delay(1000); // Kirim sinyal terus menerus setiap 1 detik
  } 
  
  // 2. Kondisi Tidak Ada Orang
  else {
    // Hanya print log jika sebelumnya ada orang (Transisi dari Ada -> Kosong)
    if (orangTerdeteksi) {
      log("SENSOR", "Objek menjauh. Stop kirim sinyal.");
      log("SENSOR", "Status: Standby...");
      orangTerdeteksi = false;
    }
    
    // Opsional: Biar serial monitor gak sepi-sepi amat, 
    // print status standby tiap 2 detik (pakai modulo)
    // if (millis() % 2000 < 50) { 
    //    log("STATUS", "Standby - Jarak: " + String(distance) + " cm");
    // }

    // Kalau mau sepi (bersih), biarkan kosong, hanya print saat event penting.
    // Tapi untuk debugging, boleh print jarak:
    // log("DEBUG", "Jarak: " + String(distance) + " cm"); 
    
    delay(500);
  }
}