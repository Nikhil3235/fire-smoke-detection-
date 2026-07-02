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
model_person = None
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
    """Load and warm up the YOLOv8 models."""
    global model, model_person
    try:
        from ultralytics import YOLO
        if not os.path.exists(weights_path):
            print(f"⚠️ Model file '{weights_path}' not found!")
            return False
        model = YOLO(weights_path)
        print("✅ YOLOv8 Custom Fire/Smoke Model Loaded Successfully!")
        
        # Load standard YOLO for person detection
        print("⏳ Loading YOLOv8n for Person Detection...")
        model_person = YOLO("yolov8n.pt") 
        print("✅ YOLOv8n Person Model Loaded Successfully!")
        
        # Warmup both models to prevent first-inference cold-start delay (takes 10-30s on CPU)
        print("⏳ Warming up YOLO models with dummy frames...")
        dummy_frame = np.zeros((320, 320, 3), dtype=np.uint8)
        model.predict(dummy_frame, imgsz=320, verbose=False)
        if model_person:
            model_person.predict(dummy_frame, imgsz=320, verbose=False)
        print("✅ Models Warmed Up Successfully! Ready for instant 0.1s predictions.")
        
        return True
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return False


HISTORY_FILE = "history.json"

def log_to_history(fire_conf, smoke_conf, people_count):
    """Log detection event to persistent history.json file."""
    import json
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fire_conf": round(fire_conf, 1),
        "smoke_conf": round(smoke_conf, 1),
        "people_count": people_count
    }
    
    history_data = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                history_data = json.load(f)
        except Exception:
            history_data = []
            
    history_data.append(entry)
    if len(history_data) > 500:
        history_data.pop(0)
        
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4)
    except Exception as e:
        print(f"Error saving history: {e}")


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


person_tracks = {}

def update_person_tracks(session_id, current_person_boxes):
    """Update tracking history for persons to identify static photos."""
    global person_tracks
    if session_id not in person_tracks:
        person_tracks[session_id] = []
        
    tracks = person_tracks[session_id]
    updated_tracks = []
    
    for box in current_person_boxes:
        x1, y1, x2, y2 = box
        best_track = None
        best_iou = 0.6
        for t in tracks:
            tx1, ty1, tx2, ty2 = t["bbox"]
            ix1 = max(x1, tx1)
            iy1 = max(y1, ty1)
            ix2 = min(x2, tx2)
            iy2 = min(y2, ty2)
            if ix1 < ix2 and iy1 < iy2:
                intersection = (ix2 - ix1) * (iy2 - iy1)
                union = (x2 - x1) * (y2 - y1) + (tx2 - tx1) * (ty2 - ty1) - intersection
                iou = intersection / union if union > 0 else 0
                if iou > best_iou:
                    best_iou = iou
                    best_track = t
                    
        if best_track:
            best_track["bbox"] = [x1, y1, x2, y2]
            best_track["history"].append([x1, y1, x2, y2])
            if len(best_track["history"]) > 15:
                best_track["history"].pop(0)
            best_track["missed_frames"] = 0
            updated_tracks.append(best_track)
            tracks.remove(best_track)
        else:
            new_track = {
                "bbox": [x1, y1, x2, y2],
                "history": [[x1, y1, x2, y2]],
                "missed_frames": 0,
                "is_static": False
            }
            updated_tracks.append(new_track)
            
    for t in tracks:
        t["missed_frames"] += 1
        if t["missed_frames"] <= 3:
            updated_tracks.append(t)
            
    for t in updated_tracks:
        if len(t["history"]) >= 8:
            xs = [h[0] for h in t["history"]]
            ys = [h[1] for h in t["history"]]
            ws = [h[2] - h[0] for h in t["history"]]
            hs = [h[3] - h[1] for h in t["history"]]
            
            std_x = np.std(xs)
            std_y = np.std(ys)
            std_w = np.std(ws)
            std_h = np.std(hs)
            
            # Static check: standard deviation in coordinates should be very small (< 1.2 pixels)
            if max(std_x, std_y, std_w, std_h) < 1.2:
                t["is_static"] = True
            else:
                t["is_static"] = False
                
    person_tracks[session_id] = updated_tracks
    
    static_boxes = []
    for t in updated_tracks:
        if t["is_static"]:
            static_boxes.append(t["bbox"])
    return static_boxes


def process_frame(frame, conf_threshold=0.4, session_id="default", draw_boxes=False):
    """Process a single frame for fire/smoke/people detection."""
    global current_fps, last_alert_time
    
    start_time = time.time()
    
    # Pitch-black sensor fix: Check average frame brightness to prevent ghost detections
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)
    if avg_brightness < 15:
        # Too dark, return immediately with empty detections to save CPU and avoid false alarms in pitch black
        return frame, []
    
    # Run detection on Person Model first (if loaded) with imgsz=640 for maximum accuracy and zero cold-start delay
    person_results = None
    if model_person:
        person_results = model_person.predict(frame, conf=0.25, imgsz=640, verbose=False)
    
    detections = []
    screen_boxes = []
    person_boxes = []
    
    # Gather raw person bboxes first
    raw_person_boxes = []
    if person_results:
        for result in person_results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0])
                if class_id == 0:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    raw_person_boxes.append([x1, y1, x2, y2])
                    
    # Identify which person boxes are static (photo frames)
    static_person_boxes = update_person_tracks(session_id, raw_person_boxes)
    
    # Process Screens and People
    if person_results:
        person_count = 1
        for result in person_results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                
                # Screen classes in COCO: 62 (tv), 63 (laptop), 67 (cell phone)
                if class_id in [62, 63, 67]:
                    if confidence > 0.3:  # Low threshold for screens to be safe against spoofing
                        screen_boxes.append((x1, y1, x2, y2))
                        
                elif class_id == 0:  # Person
                    person_boxes.append((x1, y1, x2, y2))
                    
                    # Check if this person box is static (photo frame)
                    is_static = False
                    for sbox in static_person_boxes:
                        if sbox == [x1, y1, x2, y2]:
                            is_static = True
                            break
                            
                    # Heuristic for Living vs Doll vs Static Photo
                    if confidence > 0.35 and not is_static:
                        label = f"Living Person {person_count}"
                        person_count += 1
                        box_color = (10, 255, 10)  # Green
                    else:
                        label = "Doll" if not is_static else "Photo Frame"
                        box_color = (150, 150, 160)  # Gray
                        
                    detections.append({
                        "class": label,
                        "confidence": round(confidence * 100, 1),
                        "bbox": [x1, y1, x2, y2]
                    })
                    
                    if draw_boxes:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                        cv2.putText(frame, f"{label} {confidence*100:.0f}%", (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 2)
    
    # Run detection on Fire/Smoke Model
    results = model.predict(frame, conf=conf_threshold, imgsz=320, verbose=False)
    
    fire_detected = False
    smoke_detected = False
    max_conf = 0.0
    alert_label = ""
    
    # Process Fire/Smoke
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
            fire_area = (x2 - x1) * (y2 - y1)
            
            # Anti-Spoofing Heuristic 1: Check if fire is ON a person (false positive face/shirt detection)
            is_on_person = False
            for (px1, py1, px2, py2) in person_boxes:
                ix1 = max(x1, px1)
                iy1 = max(y1, py1)
                ix2 = min(x2, px2)
                iy2 = min(y2, py2)
                if ix1 < ix2 and iy1 < iy2:
                    intersection_area = (ix2 - ix1) * (iy2 - iy1)
                    # If more than 30% of the fire box overlaps with a person, ignore it as a face/shirt false positive!
                    if fire_area > 0 and (intersection_area / fire_area) > 0.3:
                        is_on_person = True
                        break
            
            if is_on_person:
                continue  # Skip drawing this false positive entirely!
            
            # Anti-Spoofing Heuristic 2: Check if fire is ON a screen
            is_spoof = False
            for (sx1, sy1, sx2, sy2) in screen_boxes:
                # Calculate Intersection
                ix1 = max(x1, sx1)
                iy1 = max(y1, sy1)
                ix2 = min(x2, sx2)
                iy2 = min(y2, sy2)
                
                if ix1 < ix2 and iy1 < iy2:
                    intersection_area = (ix2 - ix1) * (iy2 - iy1)
                    # If more than 50% of the fire is inside a screen, it's a video/photo!
                    if fire_area > 0 and (intersection_area / fire_area) > 0.5:
                        is_spoof = True
                        break
            
            if is_spoof:
                label = f"Fake {label} (Screen)"
                box_color = (0, 165, 255)  # Orange
            else:
                if label == "Fire":
                    fire_detected = True
                    box_color = (0, 0, 255)  # Red
                elif label == "Smoke":
                    smoke_detected = True
                    box_color = (255, 120, 0)  # Blue/Orange
                    
            if confidence > max_conf:
                max_conf = confidence
                alert_label = label
                
            detections.append({
                "class": label,
                "confidence": round(confidence * 100, 1),
                "bbox": [x1, y1, x2, y2]
            })
            
            if draw_boxes:
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                cv2.putText(frame, f"{label} {confidence*100:.0f}%", (x1, y1 - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 2)
    
    # Auto-save frame and send notifications (with cooldown)
    current_time = time.time()
    session_last_alert = last_alert_time.get(session_id, 0)
    
    # Only auto-save if a real high-confidence hazard is detected to avoid false captures on background noise
    real_hazard_detected = False
    for d in detections:
        if d["class"] in ("Fire", "Smoke") and d["confidence"] >= 55.0:
            real_hazard_detected = True
            break
            
    if real_hazard_detected and (current_time - session_last_alert > ALERT_COOLDOWN):
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
        
    # Persistent History Logging on critical detection
    if fire_detected or smoke_detected:
        last_history_log = last_alert_time.get(session_id + "_history", 0)
        if current_time - last_history_log > 3.0:
            last_alert_time[session_id + "_history"] = current_time
            # Calculate actual fire/smoke max confidence
            fire_val = 0.0
            smoke_val = 0.0
            for d in detections:
                if d["class"] == "Fire":
                    fire_val = max(fire_val, d["confidence"])
                elif d["class"] == "Smoke":
                    smoke_val = max(smoke_val, d["confidence"])
            
            # Count living people
            living_people_count = sum(1 for d in detections if "Living Person" in d["class"])
            log_to_history(fire_val, smoke_val, living_people_count)
            
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
    """Generator function for video streaming with frame skipping to maintain 1.0x realtime speed."""
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
        
    # Enforce real-time playback speed for video files by skipping frames if CPU processing is slower than video FPS
    video_fps = 30.0
    total_frames = 0
    start_play_time = time.time()
    
    if camera and source not in ("webcam", "webcam1"):
        video_fps = camera.get(cv2.CAP_PROP_FPS)
        if not video_fps or video_fps <= 0:
            video_fps = 30.0
        total_frames = camera.get(cv2.CAP_PROP_FRAME_COUNT)
    
    is_detecting = True
    
    while is_detecting:
        if source not in ("webcam", "webcam1") and camera:
            # Enforce 1.0x playback speed by calculating target frame based on elapsed wall-clock time
            elapsed = time.time() - start_play_time
            target_frame = int(elapsed * video_fps)
            
            if total_frames > 0 and target_frame >= total_frames:
                # Loop video from start
                start_play_time = time.time()
                camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
            else:
                # Resilient fast frame skipping using grab() instead of slow seek
                current_frame = camera.get(cv2.CAP_PROP_POS_FRAMES)
                frames_to_skip = target_frame - current_frame
                if frames_to_skip > 0:
                    if frames_to_skip > 30:
                        camera.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    else:
                        for _ in range(int(frames_to_skip) - 1):
                            camera.grab()
                
        success, frame = camera.read()
        if not success:
            if source not in ("webcam", "webcam1"):
                # If read failed or loop ended prematurely, reset pointer
                start_play_time = time.time()
                camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            break
        
        if model:
            frame, detections = process_frame(frame, conf, draw_boxes=True)
            
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
        
        # Microscopic sleep to yield CPU cycles to Flask server upload & API request handlers
        time.sleep(0.01)
    
    if camera:
        camera.release()

# ── Flask Routes ──────────────────────────────────────────────

@app.route('/api/history')
def get_history():
    import json
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return jsonify(data)
        except Exception:
            return jsonify([])
    return jsonify([])

@app.route('/api/history/clear', methods=['POST'])
def clear_history():
    if os.path.exists(HISTORY_FILE):
        try:
            os.remove(HISTORY_FILE)
        except Exception:
            pass
    return jsonify({"success": True})

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/live')
def live():
    return send_from_directory('.', 'live.html')


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
    seq = data.get("seq", 0)
    
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
        
        # Calculate confidences and counts
        fire_conf = 0.0
        smoke_conf = 0.0
        people_count = 0
        for d in detections:
            if d["class"] == "Fire":
                fire_conf = max(fire_conf, d["confidence"])
            elif d["class"] == "Smoke":
                smoke_conf = max(smoke_conf, d["confidence"])
            elif "Person" in d["class"]:
                people_count += 1
                
        return jsonify({
            "success": True,
            "seq": seq,
            "image": processed_b64,
            "detections": detections,
            "fire_conf": fire_conf,
            "smoke_conf": smoke_conf,
            "people_count": people_count,
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
