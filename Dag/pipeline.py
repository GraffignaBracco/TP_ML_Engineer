from datetime import timedelta
from datetime import datetime
from airflow.models import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from gtfs_elt.functions import extract_gtfs, load_gtfs
import boto3, sys
import numpy as np 
import json
import pandas as pd

        
def get_max_file_with_last_year():
    s3 = boto3.client("s3")
    objects=s3.list_objects(Bucket='tpmlengineer')
    files = list()
    for obj in objects['Contents']:
        files.append(obj['Key'])
    files_tp = [x for x in files if x.startswith('tp')]
    years = [int(x.split('tp/')[1].split('.csv')[0]) for x in files_tp]
    max_year = np.array(years).max()
    file_max_year = str(max_year)
    
    return file_max_year

def download_file(data_filename):
    downloaded_data_bucket = f"tpmlengineer"
    downloaded_data_prefix = "tp"
    col_list = ['ORIGIN', 'FL_DATE', 'DEP_DELAY']
    s3 = boto3.client("s3")
    s3.download_file(downloaded_data_bucket, f"{downloaded_data_prefix}/{data_filename}", data_filename)
    df = pd.read_csv(data_filename, delimiter=",", usecols=col_list)
    return df
    
def transform_file(df):
    df_transformed = df.groupby(['ORIGIN', 'FL_DATE']).aggregate({'DEP_DELAY': ['count', 'mean']}).reset_index()
    df_transformed.columns = ['origin', 'fl_date','flights_count', 'delay_mean'] 
    return df_transformed
    
def predict_anomalies(df):
    endpoint = "randomcutforest-2022-04-01-16-34-53-759"
    sm_rt = boto3.Session().client('runtime.sagemaker') 
    
    response = sm_rt.invoke_endpoint(EndpointName=endpoint,
                                   ContentType='text/csv',
                                   Body=df.delay_mean.to_string(index=False))
    
    result = json.loads(response['Body'].read().decode())
    
    df['score'] = [x.get('score') for x in result.get('scores')]
    score_mean = df.score.mean()
    score_std = df.score.std()

    score_cutoff = score_mean + 3*score_std
    df['anomalies'] = np.where(df['score'] > score_cutoff, 1, 0)
    return df
    
def graph_airport(airport, df_anomalies, year):
    import matplotlib.pyplot as plt
    df_graph = df_anomalies.loc[df_anomalies.origin==airport,['fl_date', 'flights_count', 'anomalies']]
    df_graph.set_index('fl_date',inplace=True)
    
    outlier_dates = df_graph[df_graph['anomalies'] == 1].index
    
    y_values = [df_graph.loc[i]['flights_count'] for i in outlier_dates]
    
    fig, ax1 = plt.subplots(figsize=(30,14))

    ax1.plot(pd.to_datetime(df_graph.index), df_graph.flights_count, label='Flights')
    ax1.scatter(pd.to_datetime(outlier_dates),y_values, c='red', label='Anomalies in Delay')
    ax1.set_ylabel('Mean Delay')
    ax1.tick_params('y', colors='C0')

    ax1.legend()
    fig.suptitle( airport + ' airport delays')
    image_name = airport+".png"         
    
    plt.savefig(image_name)
    
    # upload image to aws s3
    # warning, the ACL here is set to public-read
    s3 = boto3.client("s3")
    bucket='tpmlengineer'
    img_data = open(image_name, "rb")
    s3.put_object(Bucket=bucket, Key= 'output/' + year + '/' + image_name, Body=img_data, 
                                 ContentType="image/png")
    plt.close(fig)
    
def main(year='default'):
    if year == 'default':
        year = get_last_year()
    
    data_filename = year + '.csv'
    df = download_file(data_filename)
    df_transformed = transform_file(df)
    df_anomalies = predict_anomalies(df_transformed)
    for i in df_anomalies.origin.unique():
        graph_airport(i, df_anomalies, year)

default_args = {
    'owner': 'juan',
    'retries': 0,
}

with DAG("extract_load_vehpo",default_args=default_args, catchup=False, schedule_interval=timedelta(minutes=1), start_date=datetime(2022, 1, 18, 21, 40, 0)) as dag:
    

    extract_data =  PythonOperator(

        task_id="extract_vehiclePositions",
        python_callable=_extract_gtfs,
        op_args=['vehiclePositions']
    )
     
    load_vehiclePositions =  PythonOperator(

        task_id="load_vehiclePositions",
        python_callable=_load_gtfs,
    )
    extract_vehiclePositions >> load_vehiclePositions