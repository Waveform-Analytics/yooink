import numpy as np
import pandas as pd
from munch import Munch
import importlib.resources as pkg_resources
import os
from yooink import APIClient, RequestManager


class YAMLProcessor:
    def __init__(self, yaml_file: str):
        self.yaml_file = yaml_file
        self.df_data = None

    def parse_yaml(self):
        """Load the YAML file from the package and return its content."""
        # Ensure you're only passing the file name, not the full path
        with pkg_resources.open_text(
                'yooink.request', self.yaml_file) as file:
            yaml_data = file.read()
        return Munch.fromYAML(yaml_data)

    def generate_csv(self, output_csv: str) -> None:
        """Generates CSV from the parsed YAML data."""
        yaml_data = self.parse_yaml()
        combinations = self.generate_combinations(yaml_data)
        self.df_data = pd.DataFrame(combinations)
        self.add_sensor_info()
        self.df_data.to_csv(output_csv, index=False)

    @staticmethod
    def generate_combinations(m2m_urls: Munch) -> list:
        """Generates combinations of all possible site, assembly, instrument,
        and stream methods."""
        combinations = []

        # Loop over each site in the M2M_URLS
        for site, site_data in m2m_urls.items():
            site_name = site_data.get('name')
            array = site_data.get('array')

            # Loop over each assembly in the site
            for assembly in site_data.assembly:
                assembly_name = assembly.get('name',
                                             assembly.get('subassembly'))
                assembly_type = assembly.get('type',
                                             assembly.get('subassembly'))

                # Loop over each instrument in the assembly
                for instrument in assembly.instrument:
                    instrument_class = instrument['class']
                    instrument_name = instrument.get('instrument_name')
                    instrument_model = instrument.get('instrument_model')
                    mindepth = instrument.get('mindepth')
                    maxdepth = instrument.get('maxdepth')
                    node = instrument.get('node')
                    sensor = instrument.get('sensor')

                    # Loop over each method in the instrument's stream dictionary
                    for method, stream in instrument.stream.items():
                        combinations.append({
                            'site': site, 'array': array,
                            'site_name': site_name,
                            'assembly_name': assembly_name,
                            'assembly_type': assembly_type,
                            'instrument_class': instrument_class,
                            'instrument_name': instrument_name,
                            'instrument_model': instrument_model,
                            'mindepth': mindepth, 'maxdepth': maxdepth,
                            'node': node, 'method': method,
                            'stream': stream, 'sensor': sensor
                        })

        return combinations

    def add_sensor_info(self):
        """
        Add information about the instrument location (lat/long/depth) and
        the water depth for each instrument in the table.

        Returns:
            None

        """
        latitude = []
        longitude = []
        depth = []
        water_depth = []

        # API credentials
        username = os.getenv('OOI_USER')
        token = os.getenv('OOI_TOKEN')
        # Set up the API Client and the request manager
        api_client = APIClient(username, token)
        request_manager = RequestManager(api_client)

        for idx, row in self.df_data.iterrows():
            print("Running row " + str(idx) + ' of ' +
                  str(len(self.df_data) - 1))
            deployments = request_manager.list_deployments(
                row['site'], row['node'], row['sensor'])
            if len(deployments) > 0:
                sensor_info = request_manager.get_sensor_information(
                    row['site'], row['node'], row['sensor'], deployments[0])[0]
                latitude.append(sensor_info['location']['latitude'])
                longitude.append(sensor_info['location']['longitude'])
                depth.append(sensor_info['location']['depth'])
                water_depth.append(sensor_info['waterDepth'])
            else:
                latitude.append(np.nan)
                longitude.append(np.nan)
                depth.append(np.nan)
                water_depth.append(np.nan)

        self.df_data['latitude'] = latitude
        self.df_data['longitude'] = longitude
        self.df_data['depth'] = depth
        self.df_data['water_depth'] = water_depth
