""" src/yooink/utils.py """
import numpy as np
from datetime import datetime
from typing import Union, List


def ooi_seconds_to_datetime(
        seconds_since_1900: Union[float, np.ndarray]
) -> Union[datetime, List[datetime]]:
    """
    Convert time from 'seconds since 1900-01-01 00:00' to Python datetime.

    This function accepts either a single timestamp or an array of timestamps
    in 'seconds since 1900-01-01' format and converts them to corresponding
    Python `datetime` objects (UTC).

    Args:
        seconds_since_1900: A float representing a single timestamp or a NumPy
        array of timestamps.

    Returns:
        A single Python datetime object or a list of Python datetime objects
        (UTC).
    """
    # The difference between 1900-01-01 and 1970-01-01 in seconds
    epoch_diff = 2208988800

    # Check if the input is a single value or an array
    if isinstance(seconds_since_1900, np.ndarray):
        # Convert the array to Python datetime objects
        return [datetime.utcfromtimestamp(ts - epoch_diff)
                for ts in seconds_since_1900]
    else:
        # Handle single value conversion
        return datetime.utcfromtimestamp(seconds_since_1900 - epoch_diff)

