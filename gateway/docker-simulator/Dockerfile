# Use a slim Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the simulator script
COPY init_simulator.py .

# Install a minimal set of dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Run the simulator when the container starts
CMD ["python", "init_simulator.py"]
