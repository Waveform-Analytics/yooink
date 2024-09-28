# src/yooink/__init__.py

# Import submodules
from . import api
from . import request
from . import data

# Import specific classes for direct access
from .api.client import APIClient
from .request.request_manager import RequestManager
from .data.data_manager import DataManager

# Define __all__ to control what gets imported with "from yooink import *"
__all__ = [
    'api',
    'request',
    'data',
    'APIClient',
    'RequestManager',
    'DataManager'
]
