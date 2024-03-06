FROM python:3.9

# Set the working directory
WORKDIR /app
# Copy the project files and install the dependencies
RUN chown nobody:nogroup /app
USER nobody
COPY --chown=nobody:nogroup requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -t /app/site-packages
COPY --chown=nobody:nogroup /src ./src
ENV PYTHONPATH=/app/site-packages/
# Run the Python script
CMD ["python", "src/main.py"]