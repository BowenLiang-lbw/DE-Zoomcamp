from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.google_cloud_storage import GoogleCloudStorage
from pandas import DataFrame
from os import path
import pyarrow as pa # we have included this in Docker, so it would be installed by default
import pyarrow.parquet as pq
import os # necessary for getting environment variables

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

# set an environment variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/src/dtc-de-412517-6c19c84f6d2e.json"

bucket_name = 'mage-zoomcamp-lbw-3'
project_id = 'dtc-de-412517'

table_name = "nyc_green_taxi_data"

root_path = f'{bucket_name}/{table_name}'

@data_exporter
def export_data(data, *args, **kwargs):

    table = pa.Table.from_pandas(data)

    gcs = pa.fs.GcsFileSystem()

    # partitioned by lpep_pickup_date
    pq.write_to_dataset(
        table,
        root_path=root_path,
        partition_cols=['lpep_pickup_date'],
        filesystem=gcs
    )