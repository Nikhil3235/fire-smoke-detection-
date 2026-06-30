# ============================================================
#  🔥 Fire & Smoke Detection — Model Training Script
#  Built by NIKHIL MALI
#  Architecture: YOLOv8m (Medium)
# ============================================================

from ultralytics import YOLO
import os
import argparse
from datetime import datetime


def train_model(args):
    """Train YOLOv8m model for fire and smoke detection."""
    
    print("=" * 60)
    print("🔥 FIRE & SMOKE DETECTION — MODEL TRAINING")
    print(f"   Built by NIKHIL MALI")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # ── Load Model ────────────────────────────────────────────
    if args.resume and os.path.exists(args.resume):
        print(f"\n📂 Resuming training from: {args.resume}")
        model = YOLO(args.resume)
    else:
        print(f"\n📂 Loading base model: {args.model}")
        model = YOLO(args.model)
    
    # ── Start Training ────────────────────────────────────────
    print(f"\n🚀 Training Configuration:")
    print(f"   Dataset:    {args.data}")
    print(f"   Epochs:     {args.epochs}")
    print(f"   Batch Size: {args.batch}")
    print(f"   Image Size: {args.imgsz}")
    print(f"   Device:     {args.device}")
    print(f"   Workers:    {args.workers}")
    print(f"   Project:    {args.project}")
    print(f"   Name:       {args.name}")
    print("-" * 60)
    
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        workers=args.workers,
        project=args.project,
        name=args.name,
        
        # ── Optimization ──────────────────────────────────────
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # ── Augmentation ──────────────────────────────────────
        hsv_h=0.015,        # Hue augmentation
        hsv_s=0.7,          # Saturation augmentation
        hsv_v=0.4,          # Value/brightness augmentation
        degrees=10.0,       # Rotation degrees
        translate=0.1,      # Translation
        scale=0.5,          # Scale augmentation
        shear=2.0,          # Shear augmentation
        perspective=0.0001, # Perspective augmentation
        flipud=0.5,         # Flip up-down probability
        fliplr=0.5,         # Flip left-right probability
        mosaic=1.0,         # Mosaic augmentation
        mixup=0.15,         # Mixup augmentation
        copy_paste=0.1,     # Copy-paste augmentation
        
        # ── Training Settings ─────────────────────────────────
        patience=50,        # Early stopping patience
        save=True,          # Save checkpoints
        save_period=10,     # Save every N epochs
        val=True,           # Run validation
        plots=True,         # Generate training plots
        verbose=True,       # Verbose output
        cos_lr=True,        # Cosine learning rate scheduler
        close_mosaic=10,    # Disable mosaic last N epochs
        amp=True,           # Automatic mixed precision
    )
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print(f"   Best model saved at: {args.project}/{args.name}/weights/best.pt")
    print(f"   Results saved at:    {args.project}/{args.name}/")
    print("=" * 60)
    
    return results


def validate_model(args):
    """Validate the trained model."""
    
    print("\n🔍 Running Validation...")
    
    model_path = os.path.join(args.project, args.name, "weights", "best.pt")
    if not os.path.exists(model_path):
        model_path = args.resume if args.resume else "models/best.pt"
    
    model = YOLO(model_path)
    metrics = model.val(data=args.data, imgsz=args.imgsz, device=args.device)
    
    print(f"\n📊 Validation Results:")
    print(f"   mAP@0.5:      {metrics.box.map50:.4f}")
    print(f"   mAP@0.5:0.95: {metrics.box.map:.4f}")
    print(f"   Precision:     {metrics.box.mp:.4f}")
    print(f"   Recall:        {metrics.box.mr:.4f}")
    
    return metrics


def export_model(args):
    """Export model to different formats."""
    
    print("\n📦 Exporting Model...")
    
    model_path = os.path.join(args.project, args.name, "weights", "best.pt")
    model = YOLO(model_path)
    
    # Export to ONNX
    model.export(format="onnx", imgsz=args.imgsz, simplify=True)
    print("   ✅ Exported to ONNX format")
    
    print("\n🎉 Export Complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🔥 Fire & Smoke Detection — YOLOv8m Training Script by NIKHIL MALI"
    )
    
    # Model arguments
    parser.add_argument("--model", type=str, default="yolov8m.pt",
                        help="Base model to use (default: yolov8m.pt)")
    parser.add_argument("--data", type=str, default="data.yaml",
                        help="Path to dataset YAML file")
    parser.add_argument("--resume", type=str, default=None,
                        help="Path to checkpoint to resume training")
    
    # Training arguments
    parser.add_argument("--epochs", type=int, default=100,
                        help="Number of training epochs (default: 100)")
    parser.add_argument("--batch", type=int, default=16,
                        help="Batch size (default: 16)")
    parser.add_argument("--imgsz", type=int, default=640,
                        help="Input image size (default: 640)")
    parser.add_argument("--device", type=str, default="0",
                        help="Device: 0 for GPU, cpu for CPU")
    parser.add_argument("--workers", type=int, default=8,
                        help="Number of data loader workers")
    
    # Output arguments
    parser.add_argument("--project", type=str, default="runs/train",
                        help="Project directory")
    parser.add_argument("--name", type=str, default="fire_smoke_yolov8m",
                        help="Experiment name")
    
    # Actions
    parser.add_argument("--validate", action="store_true",
                        help="Run validation after training")
    parser.add_argument("--export", action="store_true",
                        help="Export model after training")
    
    args = parser.parse_args()
    
    # Train
    results = train_model(args)
    
    # Validate
    if args.validate:
        validate_model(args)
    
    # Export
    if args.export:
        export_model(args)
