# src/yooink/__init__.py

# Import the necessary classes from their modules
from .api.client import APIClient
from .request.request_manager import RequestManager

# Optionally, define __all__ to control what's exported when 'import *' is used
__all__ = ['APIClient', 'RequestManager']
