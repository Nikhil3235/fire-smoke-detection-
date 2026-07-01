# ============================================================
#  🔥 FireVision AI — Enterprise-Grade Safety Monitoring System
#  Built by NIKHIL MALI (Computer Vision & AI Engineer)
#  Features: 
#    - Real-time YOLOv8m Fire & Smoke Inference
#    - 📱 SMS Emergency Alerts (Twilio API with Simulation Mode)
#    - 📄 PDF Report Generator (Generates downloadable PDF of all detected events)
#    - 📹 Live Session Recording (Record AI stream and download as WebM/MP4)
#    - 🔊 Web Audio API Smart Siren Alarm
#    - 📸 Auto-saving Alert Frames on detection
#    - 📊 Real-time Analytics Dashboard with Chart.js
#    - 📂 Custom File Upload for Video/Image Inference
# ============================================================

from flask import Flask, Response, jsonify, request, send_from_directory
from flask_cors import CORS
from ultralytics import YOLO
import cv2
import numpy as np
import os
import time
import threading
from datetime import datetime
import werkzeug
import requests

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ── Directories Setup ─────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALERTS_FOLDER = os.path.join(BASE_DIR, 'static', 'alerts')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ALERTS_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ── Global Variables ──────────────────────────────────────────
model = None
camera = None
is_detecting = False
current_fps = 0
detection_log = []
active_source = "webcam"

# Notification Settings (Configured via UI)
sms_config = {"enabled": False, "account_sid": "", "auth_token": "", "from_number": "", "to_number": ""}

# Alert cooldown (prevent spamming notifications)
last_alert_time = {} # dictionary keyed by session_id
ALERT_COOLDOWN = 10.0  # 10 seconds between notifications

# ── Detection Colors (BGR) ───────────────────────────────────
CLASS_COLORS = {
    0: (0, 70, 255),     # Fire (Orange-Red)
    1: (200, 200, 200),  # Smoke (Gray)
}

CLASS_NAMES = {0: "Fire", 1: "Smoke"}


def load_model(weights_path="models/best.pt"):
    """Load the YOLOv8 model."""
    global model
    try:
        from ultralytics import YOLO
        if not os.path.exists(weights_path):
            print(f"⚠️ Model file '{weights_path}' not found!")
            return False
        model = YOLO(weights_path)
        print("✅ YOLOv8 Custom Fire/Smoke Model Loaded Successfully!")
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False


def send_sms_alert(alert_type, confidence):
    """Send SMS via Twilio if enabled."""
    if not sms_config.get("enabled"):
        return
        
    message_body = f"🚨 FIREVISION AI ALERT 🚨\n{alert_type} detected with {confidence:.0%} confidence! Please check the dashboard immediately."
    
    if sms_config.get('account_sid') and sms_config.get('auth_token'):
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sms_config['account_sid']}/Messages.json"
        payload = {
            "To": sms_config['to_number'],
            "From": sms_config['from_number'],
            "Body": message_body
        }
        try:
            r = requests.post(
                url,
                data=payload,
                auth=(sms_config['account_sid'], sms_config['auth_token']),
                timeout=10
            )
            if r.status_code == 201:
                print(f"✅ Real SMS alert sent successfully to {sms_config['to_number']}!")
            else:
                print(f"❌ Twilio SMS failed: {r.text}")
        except Exception as e:
            print(f"❌ Twilio SMS error: {e}")
    else:
        # Simulation Mode
        print(f"📱 [SMS SIMULATION] Sending alert to {sms_config['to_number']}: {message_body}")


def process_frame(frame, conf_threshold=0.4, session_id="default"):
    """Process a single frame for fire/smoke detection."""
    global current_fps, last_alert_time
    
    start_time = time.time()
    
    # Run detection
    results = model.predict(frame, conf=conf_threshold, verbose=False)
    
    detections = []
    fire_detected = False
    smoke_detected = False
    max_conf = 0.0
    alert_label = ""
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            if confidence < conf_threshold:
                continue
            
            label = CLASS_NAMES.get(class_id, f"Class {class_id}")
            if label == "Fire":
                fire_detected = True
            elif label == "Smoke":
                smoke_detected = True
                
            if confidence > max_conf:
                max_conf = confidence
                alert_label = label
                
            color = CLASS_COLORS.get(class_id, (0, 255, 0))
            conf_text = f"{label} {confidence:.0%}"
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            # Label background
            (tw, th), _ = cv2.getTextSize(conf_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (x1, y1 - th - 15), (x1 + tw + 10, y1), color, -1)
            cv2.putText(frame, conf_text, (x1 + 5, y1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            detections.append({
                "class": label,
                "confidence": round(confidence * 100, 1),
                "bbox": [x1, y1, x2, y2]
            })
    
    # Auto-save frame and send notifications (with cooldown)
    current_time = time.time()
    session_last_alert = last_alert_time.get(session_id, 0)
    
    if (fire_detected or smoke_detected) and (current_time - session_last_alert > ALERT_COOLDOWN):
        last_alert_time[session_id] = current_time
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_filename = f"alert_{timestamp}.jpg"
        
        session_alert_folder = os.path.join(ALERTS_FOLDER, session_id)
        os.makedirs(session_alert_folder, exist_ok=True)
        
        alert_filepath = os.path.join(session_alert_folder, alert_filename)
        cv2.imwrite(alert_filepath, frame)
        print(f"🚨 ALERT [{session_id}]: Fire/Smoke detected! Saved frame to {alert_filepath}")
        
        # Send SMS alert in background thread
        threading.Thread(target=send_sms_alert, args=(alert_label, max_conf)).start()
        
    # Draw info overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (340, 80), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    
    end_time = time.time()
    current_fps = 1 / (end_time - start_time) if (end_time - start_time) > 0 else 0
    
    cv2.putText(frame, "FIRE & SMOKE DETECTION", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
    cv2.putText(frame, f"FPS: {current_fps:.0f} | By NIKHIL MALI", (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    
    return frame, detections


def generate_frames(source, conf=0.4):
    """Generator function for video streaming."""
    global is_detecting, camera
    
    if source == "webcam":
        camera = cv2.VideoCapture(0)
        if not camera or not camera.isOpened():
            print("⚠️ No webcam detected. Falling back to local sample fire video.")
            if camera:
                camera.release()
            source = "static/sample-fire.mp4"
            camera = cv2.VideoCapture(source)
    elif source == "webcam1":
        camera = cv2.VideoCapture(1)
        if not camera or not camera.isOpened():
            print("⚠️ No secondary webcam detected. Falling back to local sample smoke video.")
            if camera:
                camera.release()
            source = "static/sample-smoke.mp4"
            camera = cv2.VideoCapture(source)
    else:
        camera = cv2.VideoCapture(source)
    
    is_detecting = True
    
    while is_detecting:
        success, frame = camera.read()
        if not success:
            if source not in ("webcam", "webcam1"):
                camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break
        
        if model:
            frame, detections = process_frame(frame, conf)
            
            if detections:
                detection_log.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "detections": detections
                })
                if len(detection_log) > 100:
                    detection_log.pop(0)
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    
    if camera:
        camera.release()

# ── Flask Routes ──────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/video_feed')
def video_feed():
    source = request.args.get('source', 'webcam')
    conf = int(request.args.get('conf', 40)) / 100
    
    return Response(
        generate_frames(source, conf),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/stop')
def stop():
    global is_detecting, camera
    is_detecting = False
    if camera:
        camera.release()
        camera = None
    return jsonify({"status": "stopped"})


@app.route('/api/process_frame', methods=['POST'])
def api_process_frame():
    global current_fps
    data = request.json
    img_b64 = data.get("image")
    conf = float(data.get("conf", 0.4))
    session_id = data.get("session_id", "default")
    
    if not img_b64:
        return jsonify({"success": False, "error": "No image data"}), 400
        
    try:
        import base64
        import numpy as np
        import cv2
        
        if "," in img_b64:
            img_b64 = img_b64.split(",")[1]
            
        img_bytes = base64.b64decode(img_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({"success": False, "error": "Invalid image"}), 400
            
        # Process the frame
        if model:
            frame, detections = process_frame(frame, conf, session_id)
            if detections:
                detection_log.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "detections": detections
                })
                if len(detection_log) > 100:
                    detection_log.pop(0)
        else:
            detections = []
            
        return_image = data.get("return_image", True)
        processed_b64 = None
        
        if return_image:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            processed_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
        
        # Calculate confidences
        fire_conf = 0.0
        smoke_conf = 0.0
        for d in detections:
            if d["class"] == "Fire":
                fire_conf = max(fire_conf, d["confidence"])
            elif d["class"] == "Smoke":
                smoke_conf = max(smoke_conf, d["confidence"])
                
        return jsonify({
            "success": True,
            "image": processed_b64,
            "detections": detections,
            "fire_conf": fire_conf,
            "smoke_conf": smoke_conf,
            "fps": round(current_fps, 1),
            "total_detections": len(detection_log)
        })
    except Exception as e:
        print(f"Error in api_process_frame: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/debug')
def debug_status():
    import os
    res = {}
    
    # Check specific paths
    files = ["models/best.pt", "static/sample-fire.mp4", "static/sample-smoke.mp4"]
    res["checks"] = {}
    for f in files:
        exist = os.path.exists(f)
        res["checks"][f] = {
            "exists": exist,
            "size": os.path.getsize(f) if exist else 0
        }
        
    # List files in key directories
    res["root_files"] = os.listdir(".") if os.path.exists(".") else []
    res["models_files"] = os.listdir("models") if os.path.exists("models") else []
    res["static_files"] = os.listdir("static") if os.path.exists("static") else []
    
    return jsonify(res)


@app.route('/stats')
def stats():
    fire_count = 0
    smoke_count = 0
    
    if detection_log:
        last_log = detection_log[-1]
        for d in last_log.get("detections", []):
            if d["class"] == "Fire":
                fire_count += 1
            elif d["class"] == "Smoke":
                smoke_count += 1
    
    return jsonify({
        "fps": round(current_fps),
        "total_detections": len(detection_log),
        "fire_count": fire_count,
        "smoke_count": smoke_count,
        "recent_logs": detection_log[-15:]
    })


@app.route('/screenshot')
def screenshot():
    session_id = request.args.get("session_id", "default")
    if camera and camera.isOpened():
        ret, frame = camera.read()
        if ret:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_alert_folder = os.path.join(ALERTS_FOLDER, session_id)
            os.makedirs(session_alert_folder, exist_ok=True)
            path = os.path.join(session_alert_folder, f"manual_{timestamp}.jpg")
            cv2.imwrite(path, frame)
            return jsonify({"success": True, "path": path})
    return jsonify({"success": False, "error": "No active feed"})


@app.route('/api/alerts')
def get_alerts():
    """Return list of saved alert filenames."""
    session_id = request.args.get("session_id", "default")
    session_alert_folder = os.path.join(ALERTS_FOLDER, session_id)
    if not os.path.exists(session_alert_folder):
        return jsonify([])
    files = [f for f in os.listdir(session_alert_folder) if f.endswith('.jpg')]
    files.sort()
    return jsonify(files)


@app.route('/static/alerts/<session_id>/<path:filename>')
def serve_alert_image(session_id, filename):
    session_alert_folder = os.path.join(ALERTS_FOLDER, session_id)
    return send_from_directory(session_alert_folder, filename)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "No selected file"})
        
    session_id = request.form.get("session_id", "default")
    
    if file:
        filename = werkzeug.utils.secure_filename(file.filename)
        session_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_upload_folder, exist_ok=True)
        filepath = os.path.join(session_upload_folder, filename)
        file.save(filepath)
        return jsonify({"success": True, "filename": filename, "filepath": filepath})


@app.route('/api/config', methods=['POST'])
def update_config():
    """Update notification configs from UI."""
    global sms_config
    data = request.json
    
    if "sms" in data:
        sms_config.update(data["sms"])
        
    return jsonify({"success": True})


def download_sample_videos():
    """Download sample fire and smoke videos if not present."""
    samples = {
        "static/sample-fire.mp4": "https://files.catbox.moe/vz9ix2.mp4",
        "static/sample-smoke.mp4": "https://files.catbox.moe/kzn8sg.mp4"
    }
    for filepath, url in samples.items():
        if not os.path.exists(filepath):
            print(f"📥 Downloading sample video: {filepath}...")
            try:
                import urllib.request
                urllib.request.urlretrieve(url, filepath)
                print(f"✅ {filepath} downloaded successfully!")
            except Exception as e:
                print(f"❌ Failed to download {filepath}: {e}")


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 FIREVISION AI — Web Application")
    print("   Built by NIKHIL MALI")
    print("=" * 60)
    
    download_sample_videos()
    load_model("models/best.pt")
    
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🌐 Starting server at: http://localhost:{port}")
    print("   Press Ctrl+C to stop\n")
    
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
