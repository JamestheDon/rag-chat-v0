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
#RUN apt-get update && \
#    apt-get install -y openssh-server && \
#    mkdir /var/run/sshd

# Set the working directory in the container
WORKDIR /app

# Install runtime dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy the application code from the build stage
COPY --from=builder /app /app

# Ensure the documents directory is copied over
COPY --from=builder /app/documents /app/documents

# Expose ports
EXPOSE 80 

# The CMD line starts the Gunicorn server with Uvicorn workers, pointing to your FastAPI application in main.py.
#CMD ["gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:80"]
# 2 workers and 2 thr
CMD ["gunicorn", "main:app", \
     "--workers", "1", \
     "--worker-class", "custom_uvicorn_worker.CustomUvicornWorker", \
     "--bind", "0.0.0.0:80", \
     "--log-level", "info"]

