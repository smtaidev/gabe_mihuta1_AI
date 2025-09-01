FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8031

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8031"]