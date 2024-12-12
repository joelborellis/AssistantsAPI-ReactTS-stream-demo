# --------------------------
# 1. FRONTEND BUILD STAGE
# --------------------------
FROM node:18 AS frontend-builder
WORKDIR /frontend

# Copy only package files first for better caching
COPY frontend/package.json .
RUN yarn install

# Copy the rest of the frontend source code and build
COPY frontend/ .
RUN yarn build

# --------------------------
# 2. FINAL STAGE
# --------------------------
FROM python:3.11-slim

WORKDIR /

# Copy environment file
COPY .env ./

# Copy Python dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend

# Copy the Flask server code
COPY server.py .

# Copy the built frontend from the previous stage
COPY --from=frontend-builder /frontend/build ./build

# Expose a single port (e.g. 8000)
EXPOSE 8000

# Run the Flask server
CMD ["python", "server.py"]