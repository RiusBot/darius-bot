FROM python:3.8-slim-buster
#FROM freqtradeorg/freqtrade:stable


# FROM python:3.9.9-slim-bullseye as base

# # Setup env
# ENV LANG C.UTF-8
# ENV LC_ALL C.UTF-8
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONFAULTHANDLER 1
# ENV PATH=/home/ftuser/.local/bin:$PATH
# ENV FT_APP_ENV="docker"

# # Prepare environment
# RUN apt update \
#   && apt -y install sudo libatlas3-base curl sqlite3 libhdf5-serial-dev  \
#   && apt-get clean \
#   && useradd -u 1000 -G sudo -U -m -s /bin/bash ftuser \
#   && chown ftuser:ftuser /freqtrade \
#   # Allow sudoers
#   && echo "ftuser ALL=(ALL) NOPASSWD: /bin/chown" >> /etc/sudoers

# RUN git clone https://github.com/freqtrade/freqtrade.git
# WORKDIR /freqtrade

# # Install dependencies
# FROM base as python-deps
# RUN  apt-get update \
#   && apt-get -y install build-essential libssl-dev git libffi-dev libgfortran5 pkg-config cmake gcc \
#   && apt-get clean \
#   && pip install --upgrade pip

# # Install TA-lib
# COPY build_helpers/* /tmp/
# RUN cd /tmp && /tmp/install_ta-lib.sh && rm -r /tmp/*ta-lib*
# ENV LD_LIBRARY_PATH /usr/local/lib

# # Install dependencies
# COPY --chown=ftuser:ftuser requirements.txt requirements-hyperopt.txt /freqtrade/
# USER ftuser
# RUN  pip install --user --no-cache-dir numpy \
#   && pip install --user --no-cache-dir -r requirements-hyperopt.txt

# # Copy dependencies to runtime-image
# FROM base as runtime-image
# COPY --from=python-deps /usr/local/lib /usr/local/lib
# ENV LD_LIBRARY_PATH /usr/local/lib

# COPY --from=python-deps --chown=ftuser:ftuser /home/ftuser/.local /home/ftuser/.local

# USER ftuser
# # Install and execute
# COPY --chown=ftuser:ftuser . /freqtrade/

# RUN pip install -e . --user --no-cache-dir --no-build-isolation \
#   && mkdir /freqtrade/user_data/ \
#   && freqtrade install-ui


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
RUN git checkout stable
RUN chmod +x ./build_helpers/install_ta-lib.sh
RUN cd build_helpers && ./install_ta-lib.sh
RUN pip3 install -r requirements-hyperopt.txt
RUN pip3 install freqtrade


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
