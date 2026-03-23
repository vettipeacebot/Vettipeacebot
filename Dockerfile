# Use Python 3.12 slim image
FROM python:3.12-slim

# Prevent Python buffering
ENV PYTHONUNBUFFERED=1

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y \
    gcc g++ make libffi-dev libssl-dev python3-dev curl wget \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Run the bot
CMD ["python", "bot.py"]