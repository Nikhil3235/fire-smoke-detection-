---
title: FireVision AI
emoji: 🔥
colorFrom: red
colorTo: orange
sdk: docker
app_port: 7860
pinned: false
---

# 🔥 FireVision AI — Intelligent Fire & Smoke Detection System
Developed by **NIKHIL MALI** (Computer Vision & AI Engineer)

An enterprise-grade, real-time safety monitoring system powered by a custom-trained **YOLOv8m** deep learning model. Achieving **99.2% mAP** accuracy, this system is designed to detect fire and smoke hazards in real-time and trigger emergency protocols.

---

## 🌟 Key Features
- **Real-time YOLOv8m Inference:** High-speed detection of fire and smoke on live camera streams and uploaded video/image files.
- **📱 Twilio SMS Alerts:** Instant SMS notifications sent to mobile numbers when a hazard is detected (includes a simulation mode).
- **📄 PDF Safety Reports:** Generate and download detailed PDF reports containing incident snapshots and timestamps.
- **📹 Live Session Recording:** Record the AI-annotated video stream and download it as WebM/MP4.
- **🔊 Web Audio API Siren:** Dynamic in-browser audio alarm that triggers automatically on hazard detection.
- **📸 Auto-saving Alert Frames:** Instantly captures and saves high-resolution snapshots of detected hazards.
- **📊 Interactive Dashboard:** Real-time confidence tracking graphs using Chart.js.

---

## 🛠️ Tech Stack
- **AI/ML:** YOLOv8m, PyTorch, OpenCV, CUDA
- **Backend:** Flask, Python
- **Frontend:** HTML5, Vanilla CSS3 (with Premium Glassmorphism UI), JavaScript, Chart.js, jsPDF
- **CI/CD & Deployment:** GitHub Actions, Docker, Hugging Face Spaces

---

## 🚀 How to Run Locally

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/Nikhil3235/fire-smoke-detection-.git
   cd fire-smoke-detection-
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the Application:**
   ```bash
   python app.py
   ```
   Open `http://localhost:5000` in your browser.

<!-- Trigger Deploy -->
