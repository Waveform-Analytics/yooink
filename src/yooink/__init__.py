# src/yooink/__init__.py

# Import submodules
from . import api
from . import request
from . import data

# Import specific classes for direct access
from .data.data_manager import DataManager
from .api.client import APIClient, M2MInterface
from .request.request_manager import RequestManager
from .ooi_data_summary import ooi_data_summary

# Define __all__ to control what gets imported with "from yooink import *"
__all__ = [
    'api',
    'request',
    'data',
    'APIClient',
    'RequestManager',
    'DataManager',
    'M2MInterface',
    'ooi_data_summary'
]
