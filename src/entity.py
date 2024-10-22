from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    filenames: list
    source_url: str


@dataclass(frozen=True)
class DataSplitConfig:
    root_dir: Path
    target_dir: Path
    movie_filename: str
    rating_filename: str
    step: int


@dataclass(frozen=True)
class DataUpdateConfig:
    root_dir: Path
    target_dir: Path
    filenames: list
    year: int


@dataclass(frozen=True)
class DataValidationConfig:
    root_dir: Path
    movie_filename: Path
    rating_filename: Path
    STATUS_FILE: str
    movie_schema: dict
    rating_schema: dict


@dataclass(frozen=True)
class DataTransformationConfig:
    root_dir: Path
    target_dir: Path
    rating_filename: Path
    movie_filename: Path
    rating_output_filename: Path
    movie_output_filename: Path


@dataclass(frozen=True)
class ModelTrainerConfig:
    root_dir: Path
    model_name: str
    n_neighbors: int
    algorithm: str


@dataclass(frozen=True)
class ModelEvaluationConfig:
    root_dir: Path
    model_path: Path
    metric_file_name: Path
    all_params: dict
    metric_file_name: Path
    mlflow_uri: str
