FROM python:3.9

# Set the working directory
WORKDIR /app
# Copy the project files and install the dependencies
COPY /src ./src
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Run the Python script
CMD ["python", "src/main.py"]