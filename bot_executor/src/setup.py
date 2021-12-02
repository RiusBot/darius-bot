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
        "urllib3",
        "flask",
        "requests",
        "ccxt",
        "python-dateutil",
        "google-cloud-secret-manager==2.8.0",
        "firebase_admin==4.4.0"
    ]
)
