from datetime import datetime, timedelta, date
import pytz

from airflow import DAG
from airflow.decorators import task
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.python_operator import PythonOperator
from airflow import configuration as conf
from gcp import upload_directory

from stage_01_data_ingestion import DataIngestionTrainingPipeline
from stage_02_data_validation import DataValidationTrainingPipeline
from stage_03_data_transformation import DataTransformationTrainingPipeline


# Enable pickle support for XCom, allowing data to be passed between tasks
conf.set("core", "enable_xcom_pickling", "True")

# Start Dag Definition
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime.now(),
    # 'email': ['airflow@example.com'],
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

# A DAG represents a workflow, a collection of tasks
dag = DAG(
    "Data_Pipeline",
    description="This DAG represents the Data Pipeline",
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
)

# Define Operators

start_pipeline = BashOperator(task_id="start_pipeline", bash_command="pwd && ls -lart")

data_ingestion = PythonOperator(
    task_id="data_ingestion",
    python_callable=DataIngestionTrainingPipeline().main,
    provide_context=True,
    dag=dag,
)

upload_data_ingestion = PythonOperator(
    task_id="upload_data_ingestion", 
    python_callable=upload_directory,
    op_args = ['mlops-grp3-data-bucket', '/opt/airflow/dags/src/mlcore/artifacts', '', "/opt/airflow/config/gcs_key.json"] ,
    dag=dag
)

data_validation = PythonOperator(
    task_id="data_validation",
    python_callable=DataValidationTrainingPipeline().main,
    provide_context=True,
    dag=dag,
)

upload_data_validation = PythonOperator(
    task_id="upload_data_validation", 
    python_callable=upload_directory,
    op_args = ['mlops-grp3-data-bucket', '/opt/airflow/dags/src/mlcore/artifacts/data_validation', 'data_validation/', "/opt/airflow/config/gcs_key.json"] ,
    dag=dag
)


data_transformation = PythonOperator(
    task_id="data_transformation",
    python_callable=DataTransformationTrainingPipeline().main,
    provide_context=True,
    dag=dag,
)

upload_data_transformation = PythonOperator(
    task_id="upload_data_transformation", 
    python_callable=upload_directory,
    op_args = ['mlops-grp3-data-bucket', '/opt/airflow/dags/src/mlcore/artifacts/data_transformation', 'data_transformation/', "/opt/airflow/config/gcs_key.json"] ,
    dag=dag
)

end_pipeline = EmptyOperator(
    task_id="end_pipeline",
    dag=dag,
)

# Set dependencies between tasks
(
    start_pipeline
    >> data_ingestion
    # >> upload_data_ingestion
    >> data_validation
    # >> upload_data_validation
    >> data_transformation
    >> upload_data_transformation
    >> end_pipeline
)
