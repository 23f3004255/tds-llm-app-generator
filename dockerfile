# Use official lightweight Python image
FROM python:3.10-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/home/appuser/.local/bin:$PATH"

# Create non-root user
RUN useradd -m appuser

# Set working directory
WORKDIR /home/appuser/app

# Copy only requirements first for caching
COPY --chown=appuser:appuser requirements.txt .

# Switch to non-root user
USER appuser

# Install dependencies including uvicorn
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy app code
COPY --chown=appuser:appuser . .

# Expose FastAPI port
EXPOSE 8000

# Use environment file from hosting platform if provided
# (Do not copy .env into image for security)
# Example: docker run --env-file .env ...

# Command to run the app
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
