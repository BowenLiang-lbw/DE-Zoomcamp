import pandas

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test

# define a function to transform camel case into snake case
def camel_to_snake(col_name):
    snake_case = ''
    for idx, char in enumerate(col_name):
        if char.isupper() and idx > 0 and col_name[idx - 1].islower():
            snake_case += '_' + char.lower()
        else:
            snake_case += char.lower()
    return snake_case


@transformer
def transform(data, *args, **kwargs):
    
    # remove rows where the passenger count is equal to 0 or the trip distance is equal to zero
    data = data[data['passenger_count'] > 0]
    data = data[data['trip_distance'] != 0]

    # create a new column lpep_pickup_date by converting lpep_pickup_datetime to a date
    data['lpep_pickup_date'] = data['lpep_pickup_datetime'].dt.date

    # What are the existing values of VendorID in the dataset?
    print("The existing values of VendorID are: ", data['VendorID'].unique())

    # rename columns in Camel Case to Snake Case
    data.columns = [camel_to_snake(column) for column in data.columns]

    return data


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert 'vendor_id' in output.columns, "vendor_id does not exist in the DataFrame columns"
    assert output['passenger_count'].isin([0]).sum() == 0, 'There are rows with passenger count equal to zero'
    assert output['trip_distance'].isin([0]).sum() == 0, 'There are rows with trip distance equal to zero'
