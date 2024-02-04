import pandas as pd

@data_loader
def load_data_from_api(*args, **kwargs):
    """
    Template for loading data from API
    """
    url = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/green'

    taxi_dtypes = {
                    'VendorID': pd.Int64Dtype(),
                    'passenger_count': pd.Int64Dtype(),
                    'trip_distance': float,
                    'RatecodeID': pd.Int64Dtype(),
                    'store_and_fwd_flag': str,
                    'PULocationID': pd.Int64Dtype(),
                    'DOLocationID': pd.Int64Dtype(),
                    'payment_type': pd.Int64Dtype(),
                    'fare_amount': float,
                    'extra': float,
                    'mta_tax': float,
                    'tip_amount': float,
                    'tolls_amount': float,
                    'improvement_surcharge': float,
                    'total_amount': float,
                    'congestion_surcharge': float 
                }
    
    # set the date columns
    parse_dates = ['lpep_pickup_datetime', 'lpep_dropoff_datetime']

    # initialize an empty list to store dataframes for each month
    dataframes = []

    for month in range(10, 13):
        # generate the url for each month
        file_url = f"{url}/green_tripdata_2020-{month:02d}.csv.gz"
        
        # read the data for the current month
        month_data = pd.read_csv(file_url, sep=',', compression='gzip', dtype=taxi_dtypes, parse_dates=parse_dates)

        # append the dataframe to the list
        dataframes.append(month_data)

    # concatenate dataframes for all three months into a single dataframe
    final_df = pd.concat(dataframes, ignore_index=True)

    return final_df