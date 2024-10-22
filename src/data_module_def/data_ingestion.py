import os

import requests

from src.data_module_def.check_structure import (
    check_existing_file,
    check_existing_folder,
)
from src.entity import DataIngestionConfig


class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def import_raw_data(self):
        """import filenames from source_url in raw_data_relative_path"""
        if check_existing_folder(self.config.root_dir):
            os.makedirs(self.config.root_dir)

        # download all the files
        for filename in self.config.filenames:
            input_file = os.path.join(self.config.source_url, filename)
            output_file = os.path.join(self.config.root_dir, filename)
            if check_existing_file(output_file):
                object_url = input_file
                print(f"downloading {input_file} as {os.path.basename(output_file)}")
                response = requests.get(object_url)
                if response.status_code == 200:
                    # Process the response content as needed
                    content = response.text
                    text_file = open(output_file, "wb")
                    text_file.write(content.encode("utf-8"))
                    text_file.close()
                else:
                    print(
                        f"Error accessing the object {input_file}:",
                        response.status_code,
                    )
