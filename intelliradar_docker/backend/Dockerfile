# Backend Docker - FastAPI only
FROM python:3.11-slim

# Install system dependencies including Chrome prerequisites
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    gnupg \
    lsb-release \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies file
COPY requirements.txt .

# Upgrade pip to latest version
RUN pip install --upgrade pip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Google Chrome using modern GPG key management
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Set execute permissions for ChromeDriver binaries
RUN chmod +x /app/drivers/linux/chromedriver \
    && chmod +x /app/drivers/macos/chromedriver

# Configure Chrome for container environment
RUN groupadd -r chrome && useradd -r -g chrome -G audio,video chrome \
    && mkdir -p /home/chrome && chown -R chrome:chrome /home/chrome

# Expose port
EXPOSE 8000

# Set environment variables
ENV MONGODB_URL=mongodb://mongodb:27017
ENV DATABASE_NAME=intelliradar
ENV USER_DATABASE_NAME=intelliradar_users

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start FastAPI application
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]