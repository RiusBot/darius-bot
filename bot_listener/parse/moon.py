import re
import json
import base64
import logging
import functools
from .base import BaseParser


class MoonParser(BaseParser):

    def __init__(self):
        self.name = "MOON"

    def parse_symbol(self, message: str):
        return message.split('\n')[1].split(':')[1]

    def parse_action(self, message: str):
        return message.split('\n')[1].split(':')[0]
