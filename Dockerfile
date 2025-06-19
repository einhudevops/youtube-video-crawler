# Use your custom base image as the base image
FROM mglue/youtube-base-image:1.0

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
#COPY keyword.txt .

# Copy the requirements.txt file into the container
#COPY stopword.txt .

# Copy your Python project files into the container
COPY app.py .

# Run the NLP application
CMD ["python", "youtube-video-app.py"]
