#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="bot_optimizer",
    version="1.0",
    author="Yunda Tsai",
    author_email="bb04902103@gmail.com",
    packages=find_packages('.'),
    python_requires='>=3.7',
    platforms=["any"],
    install_requires=[
        "urllib3==1.26.8",
        "flask==2.0.3",
        "requests==2.27.1",
        "ccxt==1.79.94",
        "python-dateutil==2.8.2",
        "google-cloud-secret-manager==2.8.0",
        "firebase_admin==4.4.0",
        "Flask-SQLAlchemy==2.5.1",
        "PyMySQL==1.0.2",
        "mysqlclient=2.1.0",
        "pyyaml==21.10.1",
        "sqlalchemy==1.4.31",
        "freqtrade==2022.1",
        'dateparser==1.1.0'
    ]
)
