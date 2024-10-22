# -*- coding: utf-8 -*-
import os

import pandas as pd

from src.entity import DataUpdateConfig


class DataUpdate:
    def __init__(self, config: DataUpdateConfig):
        self.config = config

    def update_data(self):
        for filename in self.config.filenames:
            self.append_files(filename)

    # Append all files which names ends before a specific year
    def append_files(self, filename):
        files = [
            f
            for f in os.listdir(f"{self.config.root_dir}/{filename.split('.')[0]}")
            if f.endswith(".csv")
        ]

        dfs = []
        for file in files:
            year = int(file.split("_")[-1].split(".")[0])
            if year <= self.config.year:
                dfs.append(
                    pd.read_csv(
                        f"{self.config.root_dir}/{filename.split('.')[0]}/{file}"
                    )
                )

        df = pd.concat(dfs, ignore_index=True)
        df.to_csv(f"{self.config.target_dir}/{filename}", index=False)
