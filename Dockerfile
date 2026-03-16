FROM python:3.9-slim

# Set the working directory
WORKDIR /workspace

# Copy everything (including the 'app' folder)
COPY . .

RUN pip install -r requirements.txt

# Tell Python to look INSIDE the app folder
CMD ["python", "app/app.py"]