# Use an official lightweight Python image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install system dependencies needed for building packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc g++ libffi-dev libssl-dev && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    apt-get remove -y gcc g++ && apt-get autoremove -y && apt-get clean

# Copy the bot code
COPY . .

# Run your bot
CMD ["python", "mybot.py"]