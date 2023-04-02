#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name="bot_executor",
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
        "ccxt==3.0.23",
        "python-dateutil==2.8.2",
        "google-cloud-secret-manager==2.8.0",
        "firebase_admin==4.4.0"
    ]
)
