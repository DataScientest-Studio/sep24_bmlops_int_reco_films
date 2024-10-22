from src.common_utils import create_directories, read_yaml
from src.config import CONFIG_FILE_PATH, PARAMS_FILE_PATH, SCHEMA_FILE_PATH
from src.entity import (
    DataIngestionConfig,
    DataSplitConfig,
    DataTransformationConfig,
    DataUpdateConfig,
    DataValidationConfig,
    ModelEvaluationConfig,
    ModelTrainerConfig,
)


class ConfigurationManager:
    def __init__(
        self,
        config_filepath=CONFIG_FILE_PATH,
        params_filepath=PARAMS_FILE_PATH,
        schema_filepath=SCHEMA_FILE_PATH,
    ):
        self.config = read_yaml(config_filepath)
        self.params = read_yaml(params_filepath)
        self.schema = read_yaml(schema_filepath)

    def get_data_ingestion_config(self) -> DataIngestionConfig:
        config = self.config.data_ingestion

        create_directories([config.root_dir])

        data_ingestion_config = DataIngestionConfig(
            root_dir=config.root_dir,
            filenames=config.filenames,
            source_url=config.bucket_folder_url,
        )

        return data_ingestion_config

    def get_data_split_config(self) -> DataSplitConfig:
        config = self.config.data_split

        create_directories([config.root_dir])

        data_split_config = DataSplitConfig(
            root_dir=config.root_dir,
            target_dir=config.target_dir,
            movie_filename=config.movie_filename,
            rating_filename=config.rating_filename,
            step=config.step,
        )

        return data_split_config

    def get_data_update_config(self) -> DataUpdateConfig:
        config = self.config.data_update

        create_directories([config.target_dir])

        data_update_config = DataUpdateConfig(
            root_dir=config.root_dir,
            target_dir=config.target_dir,
            filenames=config.filenames,
            year=config.year,
        )

        return data_update_config

    def get_data_validation_config(self) -> DataValidationConfig:
        config = self.config.data_validation
        movie_schema = self.schema.MOVIE_COLUMNS
        rating_schema = self.schema.RATING_COLUMNS

        create_directories([config.root_dir])

        data_validation_config = DataValidationConfig(
            root_dir=config.root_dir,
            movie_filename=config.movie_filename,
            rating_filename=config.rating_filename,
            movie_schema=movie_schema,
            rating_schema=rating_schema,
            STATUS_FILE=config.STATUS_FILE,
        )

        return data_validation_config

    def get_data_transformation_config(self) -> DataTransformationConfig:
        config = self.config.data_transformation

        create_directories([config.target_dir])

        data_transformation_config = DataTransformationConfig(
            root_dir=config.root_dir,
            target_dir=config.target_dir,
            rating_filename=config.rating_filename,
            movie_filename=config.movie_filename,
            movie_output_filename=config.movie_output_filename,
            rating_output_filename=config.rating_output_filename,
        )

        return data_transformation_config

    def get_model_trainer_config(self) -> ModelTrainerConfig:
        config = self.config.model_trainer
        params = self.params.NearestNeighbors

        create_directories([config.root_dir])

        model_trainer_config = ModelTrainerConfig(
            root_dir=config.root_dir,
            model_name=config.model_name,
            movie_filename=config.movie_filename,
            n_neighbors=params.n_neighbors,
            algorithm=params.algorithm,
        )

        return model_trainer_config

    def get_model_evaluation_config(self) -> ModelEvaluationConfig:
        config = self.config.model_evaluation
        params = self.params.ElasticNet

        create_directories([config.root_dir])

        model_evaluation_config = ModelEvaluationConfig(
            root_dir=config.root_dir,
            model_path=config.model_path,
            metric_file_name=config.metric_file_name,
            all_params=params,
            mlflow_uri="git clone https://github.com/DataScientest-Studio/sep24_bmlops_int_reco_films.git",  # make sure to update this information
        )

        return model_evaluation_config
