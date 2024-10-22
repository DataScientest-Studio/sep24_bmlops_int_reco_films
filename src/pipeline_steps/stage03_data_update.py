import sys
from pathlib import Path

# Add parent directory to path
parent_folder = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_folder)

from custom_logger import logger
from src.config_manager import ConfigurationManager
from src.data_module_def.data_update import DataUpdate

# logging the parent directory
logger.info(f"Parent folder: {parent_folder}")

# Define stage name
STAGE_NAME = "Data Update stage"


class DataUpdatePipeline:
    def __init__(self):
        pass

    def main(self):
        config = ConfigurationManager()
        data_update_config = config.get_data_update_config()
        data_update = DataUpdate(config=data_update_config)
        data_update.update_data()


if __name__ == "__main__":
    try:
        logger.info(f">>>>> stage {STAGE_NAME} started <<<<<")
        obj = DataUpdatePipeline()
        obj.main()
        logger.info(f">>>>> stage {STAGE_NAME} completed <<<<<\n\nx=======x")

    except Exception as e:
        logger.exception(e)
        raise e
