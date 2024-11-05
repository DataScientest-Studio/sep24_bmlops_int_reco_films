# airflow/dags/monitoring_dag.py

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from src.monitoring.performance_monitor import monitor_performance
from src.monitoring.data_drift_monitor import check_data_drift
from src.monitoring.system_monitor import check_system_health
from src.monitoring.notify import send_notification

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 1, 1),
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
    'email_on_failure': True,
}

dag = DAG(
    'monitoring',
    default_args=default_args,
    description='Monitor system health and model performance',
    schedule_interval='*/30 * * * *',  # Run every 30 minutes
    catchup=False,
    tags=['monitoring', 'operations']
)

# System health monitoring
system_health_task = PythonOperator(
    task_id='check_system_health',
    python_callable=check_system_health,
    dag=dag,
)

# Performance monitoring
performance_task = PythonOperator(
    task_id='monitor_performance',
    python_callable=monitor_performance,
    dag=dag,
)

# Data drift monitoring
data_drift_task = PythonOperator(
    task_id='check_data_drift',
    python_callable=check_data_drift,
    dag=dag,
)

# Export metrics to Prometheus
export_metrics = BashOperator(
    task_id='export_metrics',
    bash_command='python /path/to/src/monitoring/export_metrics.py',
    dag=dag,
)

# Define task dependencies
system_health_task >> performance_task >> export_metrics
system_health_task >> data_drift_task >> export_metrics
