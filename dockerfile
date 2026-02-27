FROM python:3.14.2

WORKDIR /app

COPY requirements.txt .
COPY .env .env

RUN apt-get update && apt-get install -y curl unzip 
# RUN apt-get install -y xvfb # Install virtual framebuffer for headless support
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD xvfb-run -a -s "-screen 0 1920x1080x24" python app.py --worker # Use xvfb-run to run the application in a virtual display
CMD python app.py