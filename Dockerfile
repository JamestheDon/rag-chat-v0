# Build stage
FROM python:3.11-slim AS builder

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Final stage
FROM python:3.11-slim

# Install SSH server
RUN apt-get update && \
    apt-get install -y openssh-server && \
    mkdir /var/run/sshd

# Set the working directory in the container
WORKDIR /app

# Install runtime dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy the application code from the build stage
COPY --from=builder /app /app

# Expose ports
EXPOSE 80 2222

# Run the command to start your SSH server and FastAPI application
CMD service ssh start && uvicorn main:app --host 0.0.0.0 --port 80
