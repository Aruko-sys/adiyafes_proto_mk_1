import threading
from flask import Flask, request, jsonify, render_template
import pandas as pd
import cv2
import numpy as np
import time
from gaze_tracking import GazeTracking
import os

app = Flask(__name__)

gaze = GazeTracking()
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

df_columns = ['Time', 'Gaze Direction', 'Number of Faces', 'Total Violation']
df_data = pd.DataFrame(columns=df_columns)
total_violation = 0
df_lock = threading.Lock()

camera_enabled = True  # Inisialisasi status kamera aktif

# Fungsi untuk menyimpan data gaze tracking ke Excel
def autosave_data():
    pass  # tidak ada perlu autosave setiap beberapa detik

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global camera_enabled

    if not camera_enabled:
        return jsonify({"error": "Camera is disabled. Submit the exam to enable camera again."}), 400

    try:
        file = request.files['file']
    except KeyError as e:
        return jsonify({"error": "No file part in request"}), 400

    img = cv2.imdecode(np.frombuffer(file.read(), np.uint8), cv2.IMREAD_COLOR)

    # Pengecekan status kamera sebelum memproses gambar
    if camera_enabled:
        gaze.refresh(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    num_faces = len(faces)
    gaze_direction = "Fokus" if gaze.is_center() else "Not Focus"

    current_time = time.strftime('%Y-%m-%d %H:%M:%S')
    global total_violation

    # Hitung violation
    violation = 0
    if gaze_direction != "Fokus" or num_faces > 1:
        violation = 1

    total_violation += violation

    with df_lock:
        new_row = {
            'Time': current_time,
            'Gaze Direction': gaze_direction,
            'Number of Faces': num_faces,
            'Total Violation': total_violation
        }
        df_data.loc[len(df_data)] = new_row

    return jsonify({
        'gaze_direction': gaze_direction,
        'num_faces': num_faces
    })


@app.route('/submit_exam', methods=['POST'])
def submit_exam():
    global camera_enabled

    data = request.json
    if 'answers' not in data:
        return jsonify({"error": "No 'answers' key in JSON data"}), 400

    df = pd.DataFrame(data['answers'])
    exam_answers_file = 'exam_answers.xlsx'
    try:
        df.to_excel(exam_answers_file, index=False)
    except PermissionError as e:
        return jsonify({"error": f"Failed to save exam answers: {e}"}), 500

    # Simpan gaze tracking data hanya saat submit exam
    gaze_tracking_file = 'gaze_tracking_data.xlsx'
    with df_lock:
        try:
            if os.path.exists(gaze_tracking_file):
                df_existing = pd.read_excel(gaze_tracking_file)
                df_data_combined = pd.concat([df_existing, df_data], ignore_index=True)
                df_data_combined.to_excel(gaze_tracking_file, index=False)
            else:
                df_data.to_excel(gaze_tracking_file, index=False)
        except PermissionError as e:
            return jsonify({"error": f"Failed to save gaze tracking data: {e}"}), 500

    # Matikan kamera setelah submit exam
    camera_enabled = False

    return jsonify({"message": "Exam submitted successfully! Camera disabled."}), 200

if __name__ == '__main__':
    app.run()
