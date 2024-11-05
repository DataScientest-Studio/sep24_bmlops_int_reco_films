# airflow/dags/model_retraining_dag.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from src.models.retrain_model import retrain_model
from src.models.evaluate_model import evaluate_model
from src.monitoring.notify import send_notification

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'model_retraining',
    default_args=default_args,
    description='Weekly model retraining pipeline',
    schedule_interval='0 0 * * 0',  # Run at midnight every Sunday
    catchup=False,
    tags=['ml', 'recommendation']
)

def _evaluate_and_notify(**context):
    metrics = evaluate_model()
    if metrics['rmse'] > 1.0:  # threshold
        send_notification(f"Model performance degraded: RMSE={metrics['rmse']}")
    return metrics

retrain_task = PythonOperator(
    task_id='retrain_model',
    python_callable=retrain_model,
    dag=dag,
)

evaluate_task = PythonOperator(
    task_id='evaluate_model',
    python_callable=_evaluate_and_notify,
    dag=dag,
)

retrain_task >> evaluate_task
#This DAG runs weekly to retrain the model using the retrain_model function.
