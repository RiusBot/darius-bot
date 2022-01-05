import re
import json
import base64
import logging
import functools
from .base import BaseParser


class VegasParser(BaseParser):

    def __init__(self):
        self.name = "VEGAS"

    def parse_symbol(self, message: str):
        return message.split(':')[1]

    def parse_action(self, message: str):
        return message.split(':')[0]
