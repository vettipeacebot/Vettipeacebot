# Use official Python 3.12 image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install build tools for aiohttp (needed for compilation)
RUN apt-get update && apt-get install -y gcc build-essential python3-dev && \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    apt-get remove -y gcc build-essential python3-dev && \
    apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy bot code
COPY bot.py .

# Optional: copy config file if using
# COPY config.env .

# Run the bot
CMD ["python", "bot.py"]