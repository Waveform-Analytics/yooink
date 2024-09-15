"""
Get various types of sensor information for instruments that are part of
the OOI network.

"""

import requests
import os
import re


def get_site_list() -> list:
    """
    Return a list of all the sites in the system.

    Returns:
        List of strings describing the sites.

    """
