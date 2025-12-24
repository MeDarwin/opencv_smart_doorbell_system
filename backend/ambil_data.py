import cv2
import os

# Buat folder dataset jika belum ada
if not os.path.exists('dataset'):
    os.makedirs('dataset')

# Ganti angka 1 (Webcam Laptop) atau 0
cam = cv2.VideoCapture(0)
cam.set(3, 640) # Lebar video
cam.set(4, 480) # Tinggi video

# Kita pakai detektor wajah bawaan OpenCV (Haar Cascade)
# Ini otomatis download modelnya, jadi kamu tidak perlu cari file xml manual
face_detector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Masukkan ID (Angka Unik). Misal kamu = 1, Ayah = 2, Ibu = 3
face_id = input('\n Masukkan ID User (angka, misal 1): ')

print("\n [INFO] Menatap kamera... Tolong senyum! Tunggu ambil 30 foto...")
count = 0

while(True):
    ret, img = cam.read()
    if not ret: break
    
    # Ubah ke abu-abu (Syarat Face Recognition OpenCV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_detector.detectMultiScale(gray, 1.3, 5)

    for (x,y,w,h) in faces:
        cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 2)     
        count += 1
        
        # Simpan foto wajah ke folder dataset
        # Format nama file: User.ID.Urutan.jpg
        cv2.imwrite("dataset/User." + str(face_id) + '.' + str(count) + ".jpg", gray[y:y+h,x:x+w])
        cv2.imshow('Ambil Data Wajah', img)

    k = cv2.waitKey(100) & 0xff
    if k == 27: break       # Tekan ESC untuk stop manual
    elif count >= 30: break # Stop otomatis setelah 30 foto

print("\n [INFO] Selesai. Data wajah tersimpan.")
cam.release()
cv2.destroyAllWindows()