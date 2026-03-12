# 1. Use a standard Python background
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app/app.py

# 3. Copy your project files into the container
COPY . .

# 4. Install your specific requirements
RUN pip install -r requirements.txt

# 5. Keep the container running so you can code in it
CMD ["sh", "-c", "python app.py && tail -f /dev/null"]