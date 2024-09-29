# dev/yaml_to_csv.py
from yaml_processor import YAMLProcessor
import os

if __name__ == '__main__':
    processor = YAMLProcessor('m2m_urls.yml')

    output_csv = os.path.join(
        "..", "src", "yooink", "data", "data_combinations.csv")

    processor.generate_csv(output_csv)

    print("CSV generated successfully.")
