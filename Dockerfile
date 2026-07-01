# Use official Python 3.10 slim image based on Debian Bookworm
FROM python:3.10-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860

# Install system dependencies for OpenCV and YOLO
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user to avoid running as root (Hugging Face requirement)
RUN useradd -m -u 1000 user
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY --chown=user:user requirements.txt /app/

# Install CPU-only PyTorch and other requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY --chown=user:user . /app/

# Create necessary directories and set permissions
RUN mkdir -p /app/static/uploads /app/static/alerts && \
    chown -R user:user /app/static

# Switch to the non-root user
USER user

# Expose the Hugging Face Spaces port
EXPOSE 7860

# Start the Flask application
CMD ["python", "app.py"]
