# ============================================================
#  🔥 Fire & Smoke Detection — Real-Time Detection Script
#  Built by NIKHIL MALI
#  Supports: Webcam, Video File, Image, Folder
# ============================================================

from ultralytics import YOLO
import cv2
import numpy as np
import argparse
import os
import time
from datetime import datetime


# ── Detection Colors ──────────────────────────────────────────
CLASS_COLORS = {
    0: (0, 70, 255),     # Fire  → Orange-Red (BGR)
    1: (200, 200, 200),  # Smoke → Gray (BGR)
}

CLASS_NAMES = {
    0: "FIRE 🔥",
    1: "SMOKE 💨",
}


def draw_detections(frame, results, conf_threshold=0.5):
    """Draw bounding boxes and labels on frame."""
    
    detections = []
    
    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue
        
        for box in boxes:
            # Get box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            if confidence < conf_threshold:
                continue
            
            # Get color and label
            color = CLASS_COLORS.get(class_id, (0, 255, 0))
            label = CLASS_NAMES.get(class_id, f"Class {class_id}")
            conf_text = f"{label} {confidence:.1%}"
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            
            # Draw label background
            (text_w, text_h), baseline = cv2.getTextSize(
                conf_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
            )
            cv2.rectangle(
                frame, (x1, y1 - text_h - 15), (x1 + text_w + 10, y1),
                color, -1
            )
            
            # Draw label text
            cv2.putText(
                frame, conf_text, (x1 + 5, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
            )
            
            detections.append({
                "class": class_id,
                "label": label,
                "confidence": confidence,
                "bbox": [x1, y1, x2, y2]
            })
    
    return frame, detections


def draw_info_panel(frame, fps, detections, frame_count):
    """Draw info panel on top-left of frame."""
    
    h, w = frame.shape[:2]
    
    # Semi-transparent overlay
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (350, 160), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.7, frame, 0.3, 0)
    
    # Title
    cv2.putText(frame, "FIRE & SMOKE DETECTION", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 165, 255), 2)
    cv2.putText(frame, "Built by NIKHIL MALI", (20, 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    
    # Stats
    cv2.putText(frame, f"FPS: {fps:.1f}", (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)
    cv2.putText(frame, f"Frame: {frame_count}", (180, 95),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    
    # Detection counts
    fire_count = sum(1 for d in detections if d["class"] == 0)
    smoke_count = sum(1 for d in detections if d["class"] == 1)
    
    cv2.putText(frame, f"Fire: {fire_count}", (20, 125),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 70, 255), 2)
    cv2.putText(frame, f"Smoke: {smoke_count}", (160, 125),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 2)
    
    # Alert
    if fire_count > 0 or smoke_count > 0:
        alert_color = (0, 0, 255) if fire_count > 0 else (0, 165, 255)
        cv2.putText(frame, "⚠ ALERT: DETECTION ACTIVE", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, alert_color, 2)
    else:
        cv2.putText(frame, "✓ Status: Clear", (20, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return frame


def detect_webcam(model, conf_threshold=0.5, camera_id=0):
    """Run real-time detection on webcam feed."""
    
    print(f"\n📷 Starting Webcam Detection (Camera: {camera_id})...")
    print("   Press 'q' to quit | 's' to save screenshot")
    print("-" * 50)
    
    cap = cv2.VideoCapture(camera_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    if not cap.isOpened():
        print("❌ Error: Could not open webcam!")
        return
    
    frame_count = 0
    fps = 0
    prev_time = time.time()
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Error: Could not read frame!")
            break
        
        frame_count += 1
        
        # Run detection
        results = model.predict(
            frame,
            conf=conf_threshold,
            verbose=False,
            stream=False
        )
        
        # Draw detections
        frame, detections = draw_detections(frame, results, conf_threshold)
        
        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        
        # Draw info panel
        frame = draw_info_panel(frame, fps, detections, frame_count)
        
        # Show frame
        cv2.imshow("Fire & Smoke Detection — NIKHIL MALI", frame)
        
        # Key controls
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("\n👋 Detection stopped by user.")
            break
        elif key == ord('s'):
            screenshot_path = f"output/screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            cv2.imwrite(screenshot_path, frame)
            print(f"   📸 Screenshot saved: {screenshot_path}")
    
    cap.release()
    cv2.destroyAllWindows()


def detect_video(model, video_path, conf_threshold=0.5, save_output=True):
    """Run detection on a video file."""
    
    if not os.path.exists(video_path):
        print(f"❌ Error: Video file not found: {video_path}")
        return
    
    print(f"\n🎬 Processing Video: {video_path}")
    print("   Press 'q' to quit")
    print("-" * 50)
    
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"   Resolution: {width}x{height}")
    print(f"   FPS: {video_fps}")
    print(f"   Total Frames: {total_frames}")
    
    # Setup video writer for output
    writer = None
    if save_output:
        output_path = f"output/detected_{os.path.basename(video_path)}"
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, video_fps, (width, height))
        print(f"   Output: {output_path}")
    
    frame_count = 0
    prev_time = time.time()
    fps = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Run detection
        results = model.predict(
            frame,
            conf=conf_threshold,
            verbose=False,
            stream=False
        )
        
        # Draw detections
        frame, detections = draw_detections(frame, results, conf_threshold)
        
        # Calculate FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time
        
        # Draw info panel
        frame = draw_info_panel(frame, fps, detections, frame_count)
        
        # Progress
        progress = (frame_count / total_frames) * 100
        print(f"\r   Processing: {progress:.1f}% ({frame_count}/{total_frames})", end="")
        
        # Save output frame
        if writer:
            writer.write(frame)
        
        # Show frame
        cv2.imshow("Fire & Smoke Detection — NIKHIL MALI", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n\n👋 Detection stopped by user.")
            break
    
    print(f"\n\n✅ Video processing complete! ({frame_count} frames)")
    
    cap.release()
    if writer:
        writer.release()
        print(f"   📹 Output saved: {output_path}")
    cv2.destroyAllWindows()


def detect_image(model, image_path, conf_threshold=0.5, save_output=True):
    """Run detection on a single image."""
    
    if not os.path.exists(image_path):
        print(f"❌ Error: Image not found: {image_path}")
        return
    
    print(f"\n🖼️  Processing Image: {image_path}")
    
    frame = cv2.imread(image_path)
    
    # Run detection
    results = model.predict(
        frame,
        conf=conf_threshold,
        verbose=False
    )
    
    # Draw detections
    frame, detections = draw_detections(frame, results, conf_threshold)
    
    # Draw info
    frame = draw_info_panel(frame, 0, detections, 1)
    
    print(f"   Detections found: {len(detections)}")
    for d in detections:
        print(f"   → {d['label']} ({d['confidence']:.1%})")
    
    # Save output
    if save_output:
        output_path = f"output/detected_{os.path.basename(image_path)}"
        cv2.imwrite(output_path, frame)
        print(f"   📸 Output saved: {output_path}")
    
    # Show
    cv2.imshow("Fire & Smoke Detection — NIKHIL MALI", frame)
    print("   Press any key to close...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def detect_folder(model, folder_path, conf_threshold=0.5):
    """Run detection on all images in a folder."""
    
    if not os.path.isdir(folder_path):
        print(f"❌ Error: Folder not found: {folder_path}")
        return
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
    images = [f for f in os.listdir(folder_path) 
              if f.lower().endswith(image_extensions)]
    
    print(f"\n📂 Processing Folder: {folder_path}")
    print(f"   Found {len(images)} images")
    print("-" * 50)
    
    for i, img_name in enumerate(images, 1):
        img_path = os.path.join(folder_path, img_name)
        print(f"\n   [{i}/{len(images)}] {img_name}")
        
        frame = cv2.imread(img_path)
        results = model.predict(frame, conf=conf_threshold, verbose=False)
        frame, detections = draw_detections(frame, results, conf_threshold)
        
        output_path = f"output/detected_{img_name}"
        cv2.imwrite(output_path, frame)
        
        print(f"   → {len(detections)} detections → saved to output/")
    
    print(f"\n✅ All {len(images)} images processed!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🔥 Fire & Smoke Detection — Real-Time Inference by NIKHIL MALI"
    )
    
    parser.add_argument("--model", type=str, default="models/best.pt",
                        help="Path to trained model weights (default: models/best.pt)")
    parser.add_argument("--source", type=str, default="webcam",
                        help="Input source: 'webcam', video path, image path, or folder path")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Confidence threshold (default: 0.5)")
    parser.add_argument("--camera", type=int, default=0,
                        help="Camera ID for webcam (default: 0)")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save output")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔥 FIRE & SMOKE DETECTION SYSTEM")
    print("   Built by NIKHIL MALI")
    print("   Architecture: YOLOv8m")
    print("=" * 60)
    
    # Load model
    if not os.path.exists(args.model):
        print(f"\n❌ Model not found: {args.model}")
        print("   Please train the model first using train.py")
        print("   Or place your trained 'best.pt' in the models/ folder")
        exit(1)
    
    print(f"\n📂 Loading model: {args.model}")
    model = YOLO(args.model)
    print("✅ Model loaded successfully!")
    
    # Create output directory
    os.makedirs("output", exist_ok=True)
    
    # Run detection based on source
    source = args.source.lower()
    save = not args.no_save
    
    if source == "webcam":
        detect_webcam(model, args.conf, args.camera)
    elif os.path.isfile(args.source):
        ext = os.path.splitext(args.source)[1].lower()
        if ext in ('.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'):
            detect_video(model, args.source, args.conf, save)
        elif ext in ('.jpg', '.jpeg', '.png', '.bmp', '.webp'):
            detect_image(model, args.source, args.conf, save)
        else:
            print(f"❌ Unsupported file format: {ext}")
    elif os.path.isdir(args.source):
        detect_folder(model, args.source, args.conf)
    else:
        print(f"❌ Invalid source: {args.source}")
        print("   Use 'webcam', a video/image file path, or a folder path")
