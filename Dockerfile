# Use Python 3.12 slim image
FROM python:3.12-slim

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the bot code
COPY . .

# Command to run your bot
CMD ["python", "bot.py"]