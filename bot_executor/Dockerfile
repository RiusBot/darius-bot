FROM python:3.8-slim-buster

# System packages installation
RUN apt update -y
RUN apt install -y \
    apt-utils \
    curl \
    gnupg2 \
    ca-certificates \
    lsb-release \
    libglib2.0-0 \
    libgtk2.0-dev \
    libsm6 \
    libxext6 \
    libxrender-dev

# API dependecies + config
RUN pip3 install gunicorn==20.0.4

# Copy and install source
COPY ./bot_executor/src/ /opt/bot_executor/

RUN pip3 install -e /opt/bot_executor/

WORKDIR /opt/bot_executor/

EXPOSE 8080

CMD exec gunicorn bot_executor.flask_app:app \
        --bind :$PORT \
        --workers 5 \
        --threads 1 \
        --timeout 3600
