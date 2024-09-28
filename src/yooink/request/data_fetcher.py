# src/yooink/request/data_fetcher.py

from yooink import APIClient, RequestManager, DataManager
from yooink.request import M2M_URLS

import os
from typing import List, Dict, Optional, Any
import xarray as xr
import numpy as np
import pytz
from dateutil import parser


class DataFetcher:
    def __init__(self, username=None, token=None) -> None:
        """ Initialize the DatasetFetcher. """
        self.username = username or os.getenv('OOI_USER')
        self.token = token or os.getenv('OOI_TOKEN')
        self.api_client = APIClient(self.username, self.token)
        self.data_manager = DataManager()
        self.request_manager = RequestManager(
            self.api_client, use_file_cache=True)

    @staticmethod
    def filter_urls(
            site: str,
            assembly: str,
            instrument: str,
            method: str
    ) -> tuple[List[str], List[str], List[str]]:
        """
        Filters the M2M_URLS dictionary for the instrument of interest.

        This function searches for the instrument of interest as defined by the
        site code, assembly type, instrument class, and data delivery method to
        return the OOI specific site, node and stream names needed to
        request the data.

        Args:
            site: OOI eight letter site code (e.g. CE04OSPS for the Oregon
                Offshore Shallow Profiler)
            assembly: Assembly grouping name (e.g. midwater for the 200 m
                Platform)
            instrument: The instrument class name (e.g. phsen for the
                SAMI2-pH sensor)
            method: The data delivery method (e.g. streamed for cabled
                streaming data)

        Returns:
            A tuple containing three lists:
                - node: The OOI specific node code(s) for the assembly
                - sensor: The OOI specific sensor code(s) for the instrument
                    class
                - stream: The OOI specific stream name(s) for the site, node,
                    sensor and delivery method combination

        Raises:
            SyntaxError: If an unknown site code or data delivery method is
                provided.
            RuntimeWarning: If the instrument defined by the given parameters
                cannot be found.
        """
        node: List[str] = []
        sensor: List[str] = []
        stream: List[str] = []

        # Pare the larger dictionary down to the site of interest and check if
        # a valid site was used
        m2m_urls: Dict[str, Any] = M2M_URLS.get(site.upper())
        if not m2m_urls:
            raise SyntaxError(f'Unknown site code: {site}')

        # Make sure the correct data delivery method was specified
        valid_methods = ['streamed', 'telemetered', 'recovered_host',
                         'recovered_inst', 'recovered_cspp', 'recovered_wfp']
        if method not in valid_methods:
            raise SyntaxError(f'Unknown data delivery method: {method}')

        # Find the instrument(s) of interest in the assembly group
        for grouping in m2m_urls.get('assembly', []):
            if grouping.get('type') == assembly or grouping.get(
                    'subassembly') == assembly:
                for instrmt in grouping['instrument']:
                    if instrmt['class'] == instrument:
                        node.append(instrmt.node)
                        sensor.append(instrmt.sensor)
                        stream.append(instrmt.stream.get(method))

        # Check to see if we were able to find the system of interest
        if not stream:
            raise RuntimeWarning(
                f'Instrument defined by {site}-{assembly}-{instrument}-'
                f'{method} cannot be found.')

        # Return the OOI specific names for the node(s), sensor(s) and
        # stream(s)
        return node, sensor, stream

    def get_dataset(
            self,
            site: str,
            assembly: str,
            instrument: str,
            method: str,
            **kwargs: Any
    ) -> xr.Dataset:
        """
        Requests data via the OOI M2M API using the site code, assembly type,
        instrument class and data delivery method.

        This function constructs the OOI specific data request using the
        parameters defined in the m2m_urls.yml file.

        Args:
            site: OOI site code as an 8 character string
            assembly: The assembly type where the instrument is located
            instrument: The OOI instrument class name for the instrument of
                interest
            method: The data delivery method for the system of interest
            **kwargs: Optional keyword arguments:
                start: Starting date/time for the data request in a
                    dateutil.parser recognizable form. If None, the beginning
                    of the data record will be used.
                stop: Ending date/time for the data request in a
                    dateutil.parser recognizable form. If None, the end of
                    the data record will be used.
                deploy: Use the deployment number (integer) to set the starting
                    and ending dates. If None, the starting and ending dates
                    are used. If both are provided, the deployment number
                    takes priority.
                aggregate: In cases where more than one instance of an
                    instrument class is part of an assembly, will collect
                    all the data if 0, or the specific instance of the
                    instrument if any value greater than 0 is used. If None,
                    the first instance of an instrument will be used.

        Returns:
            An xarray dataset containing the requested data for further
            analysis.

        Raises:
            KeyError: If an unknown keyword argument is provided.
            SyntaxError: If the date string format is unrecognizable or if an
                invalid aggregate value is provided.
            RuntimeWarning: If deployment dates are unavailable or if data is
                unavailable for the specified parameters.
        """
        # Setup inputs to the function, make sure case is correct
        site = site.upper()
        assembly = assembly.lower()
        instrument = instrument.lower()
        method = method.lower()

        # Parse the keyword arguments
        start: Optional[str] = None
        stop: Optional[str] = None
        deploy: Optional[int] = None
        aggregate: Optional[int] = None
        for key, value in kwargs.items():
            if key not in ['start', 'stop', 'deploy', 'aggregate']:
                raise KeyError(f'Unknown keyword ({key}) argument.')
            else:
                if key == 'start':
                    start = value
                if key == 'stop':
                    stop = value
                if key == 'deploy':
                    deploy = value
                if key == 'aggregate':
                    aggregate = value

        # Use the assembly, instrument and data delivery methods to find the
        # system of interest
        node, sensor, stream = self.filter_urls(
            site, assembly, instrument, method)

        # Check the formatting of the start and end dates. We need to be able
        # to parse and convert to an ISO format.
        if start:
            try:
                start = parser.parse(start)
                start = start.astimezone(pytz.utc)
                start = start.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            except parser.ParserError:
                raise SyntaxError(
                    'Formatting of the starting date string needs to be in a '
                    'recognizable format')

        if stop:
            try:
                stop = parser.parse(stop)
                stop = stop.astimezone(pytz.utc)
                stop = stop.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            except parser.ParserError:
                raise SyntaxError(
                    'Formatting of the ending date string needs to be in a '
                    'recognizable format')

        if deploy:
            # Determine start and end dates based on the deployment number
            start, stop = self.request_manager.get_deployment_dates(
                site, node[0], sensor[0], deploy)
            if not start or not stop:
                exit_text = (
                    f'Deployment dates are unavailable for {site.lower()}-'
                    f'{assembly}-{instrument}-{method}, '
                    f'deployment {deploy:02d}.')
                raise RuntimeWarning(exit_text)

        # For some cases, there may be more than 1 stream, but in general,
        # we only want the first one
        stream = stream[0][0] if isinstance(stream[0], list) else stream[0]

        tag = f'.*{instrument.upper()}.*\\.nc$'  # set regex tag
        data: Optional[xr.Dataset] = None  # setup the default data set

        # Check if there are multiple instances of this instrument class on the
        # assembly
        if len(node) > 1:
            print(
                f'There are multiple instances of the instrument {instrument} '
                f'under {site.lower()}-{assembly}.')

        # Check if we are aggregating the multiple instruments into a single
        # data set
        if isinstance(aggregate, int):
            if aggregate == 0:
                print(
                    f'Requesting all {len(node)} instances of this '
                    f'instrument. Data sets will be concatenated\n'
                    'and a new variable called `sensor_count` will be added '
                    'to help distinguish the \n'
                    'instruments for later processing.')
                for i in range(len(node)):
                    temp = self.request_manager.fetch_data(
                        site, node[i], sensor[i], method, stream, start, stop,
                        tag=tag
                    )
                    temp['sensor_count'] = temp['deployment'] * 0 + i + 1
                    if not data:
                        data = temp
                    else:
                        data = xr.concat([data, temp], dim='time')
            else:
                if aggregate > len(node):
                    raise SyntaxError(
                        f'Only {len(node)} instruments available, you '
                        f'selected {aggregate}')

                print(f'Requesting instrument {aggregate} out of {len(node)}.')
                i = aggregate - 1
                data = self.request_manager.fetch_data(
                    site, node[i], sensor[i], method, stream, start, stop,
                    tag=tag
                )

        else:
            data = self.request_manager.fetch_data(
                site, node[0], sensor[0], method, stream, start, stop,
                tag=tag
            )

        if not data:
            raise RuntimeWarning(
                f'Data unavailable for {site.lower()}-{assembly}-'
                f'{instrument}-{method}.')

        # Convert strings with data types set as objects or S64 with binary
        # encoding
        for v in data.variables:
            if data[v].dtype == np.dtype('O') or data[v].dtype == np.dtype(
                    'S64'):
                data[v] = data[v].astype(np.str_)

        return data
