import pandas as pd
from munch import Munch
import importlib.resources as pkg_resources


class YAMLProcessor:
    def __init__(self, yaml_file: str):
        self.yaml_file = yaml_file

    def parse_yaml(self):
        """Load the YAML file from the package and return its content."""
        # Ensure you're only passing the file name, not the full path
        with pkg_resources.open_text(
                'yooink.request', self.yaml_file) as file:
            yaml_data = file.read()
        return Munch.fromYAML(yaml_data)

    def generate_csv(self, output_csv: str):
        """Generates CSV from the parsed YAML data."""
        yaml_data = self.parse_yaml()
        combinations = self.generate_combinations(yaml_data)
        df = pd.DataFrame(combinations)
        df.to_csv(output_csv, index=False)

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

                    # Loop over each method in the instrument's stream dictionary
                    for method, stream in instrument.stream.items():
                        combinations.append({'site': site, 'array': array,
                            'site_name': site_name,
                            'assembly_name': assembly_name,
                            'assembly_type': assembly_type,
                            'instrument_class': instrument_class,
                            'instrument_name': instrument_name,
                            'instrument_model': instrument_model,
                            'mindepth': mindepth, 'maxdepth': maxdepth,
                            'node': node, 'method': method, 'stream': stream})

        return combinations
