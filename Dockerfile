# Use an official Python runtime as a parent image
# We choose a lightweight, smaller image based on Alpine Linux
FROM python:3.12-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies specified in requirements.txt
# The --no-cache-dir flag reduces the image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
# This includes main.py and any other necessary files
COPY . .

# Command to run the application
# This executes your bot script when the container starts
CMD ["python", "main.py"]
