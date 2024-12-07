FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Copy and install requirements
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install SQLite
RUN apt-get update && apt-get install -y --no-install-recommends sqlite3 && apt-get clean

# Copy project files into the container
COPY . /app/

# Expose the application port
EXPOSE 8080

# Entrypoint for running the application
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8080"]