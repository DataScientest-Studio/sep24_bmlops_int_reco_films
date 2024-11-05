from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from src.monitoring.performance_monitor import monitor_performance

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'performance_monitoring',
    default_args=default_args,
    description='A DAG for monitoring model performance',
    schedule_interval=timedelta(hours=1),
)

monitor_task = PythonOperator(
    task_id='monitor_performance',
    python_callable=monitor_performance,
    dag=dag,
)
