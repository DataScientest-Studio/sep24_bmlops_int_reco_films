# airflow/dags/data_subset_creation_dag.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.sensors.filesystem import FileSensor
from datetime import datetime, timedelta
from src.data.create_subset import create_training_subset
from src.monitoring.notify import send_notification

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
}

dag = DAG(
    'data_subset_creation',
    default_args=default_args,
    description='Create training data subsets daily',
    schedule_interval='0 1 * * *',  # Run at 1 AM daily
    catchup=False,
    tags=['data', 'preprocessing']
)

# Check if source data exists
check_data = FileSensor(
    task_id='check_source_data',
    filepath='/path/to/data/processed/processed_data.csv',
    poke_interval=300,
    timeout=1200,
    mode='poke',
    dag=dag,
)

def _create_subset_with_notification(**context):
    try:
        create_training_subset(
            processed_data_path='/path/to/data/processed/processed_data.csv',
            subset_path='/path/to/data/subsets/subset.csv',
            sample_size=10000,
            stratify_column='rating'
        )
        send_notification("Data subset created successfully")
    except Exception as e:
        send_notification(f"Error creating data subset: {str(e)}")
        raise

create_subset_task = PythonOperator(
    task_id='create_subset',
    python_callable=_create_subset_with_notification,
    dag=dag,
)

check_data >> create_subset_task
# This DAG runs daily and triggers the creation of a new training subset using the create_training_subset function.
