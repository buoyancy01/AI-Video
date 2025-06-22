# Stage 1: Use a specific, stable base image
FROM python:3.11-slim as base

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
# Ensure Python output is sent straight to the terminal
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Copy only the requirements file first
COPY requirements.txt .

# Install dependencies. This layer will only be invalidated
# if requirements.txt changes.
RUN pip install --no-cache-dir -r requirements.txt

# Now, copy the rest of your application code.
# Changes to your .py files will only invalidate this layer
# and subsequent ones, not the dependency installation.
COPY . .

# --- Best Practices for Production ---

# Create a non-root user to run the application for security
RUN addgroup --system nonroot && adduser --system --ingroup nonroot nonroot
USER nonroot

# Expose the port the app runs on
EXPOSE 5000

# Use a production-grade WSGI server like Gunicorn, not Flask's dev server
# The command for Render should be set to this.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
