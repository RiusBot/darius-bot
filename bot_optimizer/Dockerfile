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
    libxrender-dev \
    default-libmysqlclient-dev \
    git


# Freqtrade
RUN git clone https://github.com/freqtrade/freqtrade.git
WORKDIR freqtrade
RUN git checkout tags/2022.5
RUN chmod +x ./build_helpers/install_ta-lib.sh
RUN cd build_helpers && ./install_ta-lib.sh
RUN pip3 install -r requirements-hyperopt.txt
RUN pip3 install freqtrade==2022.5
RUN pip3 install -U numpy


# API dependecies + config
RUN pip3 install gunicorn==20.0.4

# Copy and install source
COPY ./bot_optimizer/src/ /opt/bot_optimizer/


RUN pip3 install -e /opt/bot_optimizer/

WORKDIR /opt/bot_optimizer/

EXPOSE 8080

CMD exec gunicorn bot_optimizer.flask_app:app \
        --bind :$PORT \
        --workers 5 \
        --threads 1 \
        --timeout 3600
