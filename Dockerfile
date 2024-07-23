# Use the official Python base image
FROM python:3.12-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Build prisma client
RUN prisma generate

# Expose the port your app runs on
EXPOSE 8000

# Define the command to run when the container starts
CMD ["uvicorn", "main:app", "--port", "$PORT", "--host", "0.0.0.0"]