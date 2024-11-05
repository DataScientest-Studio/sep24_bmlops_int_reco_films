# airflow/dags/model_evaluation_dag.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.sensors.filesystem import FileSensor
from datetime import datetime, timedelta
from src.models.evaluate_model import evaluate_model
from src.monitoring.metrics import log_metrics_to_mlflow
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
    'model_evaluation',
    default_args=default_args,
    description='Evaluate model performance daily',
    schedule_interval='0 2 * * *',  # Run at 2 AM daily
    catchup=False,
    tags=['ml', 'evaluation']
)

# Check if model exists
check_model = FileSensor(
    task_id='check_model_file',
    filepath='/path/to/models/trained_models/current_model.pkl',
    poke_interval=300,
    timeout=1200,
    mode='poke',
    dag=dag,
)

def _evaluate_and_log(**context):
    try:
        metrics = evaluate_model(
            data_path='/path/to/data/evaluation/eval_set.csv',
            model_path='/path/to/models/trained_models/current_model.pkl'
        )
        
        # Log metrics to MLflow
        log_metrics_to_mlflow(metrics)
        
        # Check performance thresholds
        if metrics['rmse'] > 1.0 or metrics['mae'] > 0.8:
            send_notification(
                f"Model performance below threshold: RMSE={metrics['rmse']}, MAE={metrics['mae']}"
            )
        
        return metrics
    except Exception as e:
        send_notification(f"Error during model evaluation: {str(e)}")
        raise

evaluate_task = PythonOperator(
    task_id='evaluate_model',
    python_callable=_evaluate_and_log,
    dag=dag,
)

check_model >> evaluate_task

#This DAG evaluates the current model daily.

#This DAG triggers the monitoring scripts hourly.
