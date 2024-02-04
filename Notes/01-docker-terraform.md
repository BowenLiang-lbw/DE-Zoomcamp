[TOC]

# Docker + Postgres

***Data Engineering***  is the design and development of systems for collecting, storing and analyzing data at scale.

## Basic Knowledge

### Architecture

During the course we will replicate the following architecture:

- New York's Taxi and Limousine Corporation's Trip Records Dataset: the dataset we will use during the course.
- Spark: analytics engine for large-scale data processing (distributed processing)
- Google BigQuery: serverless data warehouse (central repository of integrated data from one or more disparate sources).
- Kafka: unified, high-throughput,low-latency platform for handling real-time data feeds (streaming).

### Data pipelines

A **data pipeline** is a service that receives data as input and outputs more data. For example, reading a CSV file, transforming the data somehow and storing it as a table in a PostgreSQL database.

![data_pipeline](./image-01/data-pipeline.png)

## Introduction to Docker

### Introduction

**Docker** delivers software in packages called **container** and containers are isolated from others.

Docker provides us with **reproducibility**. Docker image is like a snapshot which can be run in different environment.

Why should we care about docker?

- Reproducibility
- Local experiments
- Integration tests (CI/CD): we run a series of tests on a data pipeline to ensure that its behavior aligns with expectations. The tests include running the data pipeline against a database, verifying the presence of expected records, and confirming the absence of records that shouldn't be there.
- Running pipelines on the cloud (AWS Batch, Kubernetes jobs): run our image on the cloud.
- Spark: we can specify all the dependencies we need for our data pipeline in spark with docker.
- Serverless (AWS Lambda, Google functions): processing data usually one record at a time. AWS Lambda usually let us define the environment also as a docker image.

### Practice

#### Practice 1: Ubuntu

Run the following command in terminal:

```bash
docker run -it ubuntu bash
```

- `docker run`: run a new container
- `-it`: run in an interactive mode
  - `-i`: interactive
  - `-t`: allocate a pseudo-TTY (terminal) for the container

- `ubuntu`: the name of the docker image
- `bash`: default shell launched inside the container. Bash is a parameter to the container which we want to execute in this image. Everything comes after the image name is parameter to this container.

![docker-ubuntu](/Users/lbw1125/Desktop/DE-Zoomcamp/Notes/image-01/docker-ubuntu.png)

We can do an experiment, remove all the things in the image:

```bash
rm -rf / --no-preserve-root
```

- `rm`: remove files and directories
- `-rf`: parameters
  - `-r`: recursively remove directories and their content
  - `-f`: force removal without confirmation

- `/`: the root directory
- `--no-preserve-root`: bypasses the safeguards, forcefully executing the deletion of the root directory

Now the image is empty:

![rm-all-files](./image-01/rm-all-files.png)

Exit the container and run it again, we will be back to the state that we were before. Everything is here and the container is not affected. This is what **isolation** means. If an app does something stupid, the host machine is not affected. Everytime we exit and rerun the `docker run` command, we will start a new container.

![new-docker-ubuntu](./image-01/new-docker-ubuntu.png)

#### Practice 2: python

Let's run another command:

```bash
docker run -it python:3.9
```

![docker-python](./image-01/docker-python1.png)

If we want use `pandas` library, we need to install it. We can use `pip install pandas` but we need to run this command outside of python prompt.

Exit using `ctrl+d`, we need to get to ***bash*** to be run the install command. **Entry point** is what exactly is executed when we run the container. We can overwrite the default entry point to ***bash*** instead of the ***python interpreter***.

```bash
docker run -it --entrypoint=bash python:3.9
```

![run-pandas](./image-01/run-pandas.png)

Now we can go to the python prompt and execute the following commands, and we can see pandas is available to use.

![python-pip](./image-01/python-pip.png)

If we exit the container and rerun the command, it will start a new container where we don't have pandas available. So somehow we need to add pandas to make sure that pandas is there when we run our code.

We need to build a docker file, where we can specify all the instructions we want to run and build a new image.

```dockerfile
# base Docker image that we will built on
FROM pyhton:3.9

# set up out image by installing prerequisites; pandas in this case
RUN pip install pandas

# define what to do first when the container runs
# here we us 'bash'
ENTRYPOINT ["bash"]
```

Run the following command to build the docker image:

```bash
docker build -t test:pandas .
```

- `docker build`: build docker image
- `-t`: assgin a tag for the image
- `test`: name of the repository of the image
- `pandas`: name of the tage
- `.`: build the image in the current directory (it will look for Dockerfile in this directory and execute it)

After finishing building the image, run this:

```bash
docker run -it test:pandas
```

![run-pandas-2](./image-01/run-pandas-2.png)

We can see that `pandas` is available for use.

#### Practice 3: pipeline

Let's create a pipeline. We will create a dummy `pipeline.py` python script that receives an argument and prints it. First we just want to check that 

```python
import sys
# we don't actually need this but it's useful for the example
import pandas as pd

# print arguments
print(sys.argv)

# argument 0 is the name of the file
# argument 1 contains the actual first argument we care about
day = sys.argv[1]

#some fancy stuff with pandas

# print a sentence with the argument
print(f'job finished successfully for day = {day}')
```

`sys.argv` is a list provided by `sys` module that contains command-line arguments. The first elemennt is **the script's name**, and the subsequent elements are the **command-line parameters** provided when running the script.

```bash
python pipeline.py argument1 argument2
```

Create the following `Dockerfile` file:

```dockerfile
# base Docker image
FROM python:3.9

# set up our image by installing prerequistes
RUN pip install pandas

# set up the working directory inside the container
# it will do `cd /app` to the directory and copy the file there
# when we run the container we will be in `/app` directory and have our `pipeline.py` file
WORKDIR /app

# copy the script to the container
# 1st name is source file
# 2nd is destination
COPY pipeline.py pipeline.py

# define what to do first when the container runs
# here we just run the script
ENTRYPOINT [ "python", "pipeline.py" ]
```

Run the following commands to build the image:

```bash
docker build -t test:pandas .
```

- `test`: name of the image
- `pandas`: name of its tag, and if not specified it will default to `latest`

Now we can run the container and pass an argument to it, such as '2024-01-17':

```bash
docker run -it test:pandas 2024-01-17
```

Here if you run the following command:

```bash 
docker run my_image arg1 arg2
```

It's equivalent to:

```bash
python pipeline.py arg1 arg2
```

> Note: these instructions asume that `pipeline.py` and `Dockerfile` are in the same directory. The Docker commands should also be run from the same directory as these files.



## Ingesting NY Taxi Data to Postgres

### Running Postgres with docker

To run Postgres with Docker, we will use the official docker image. We can run a containerized version of Postgres that doesn't require any installation steps. You only need to provide a few **environment variables** to it and a **volume** for storing data. Volume is a way of mapping folder that we have in our file system on the host machine to a folder in the container.

Postgres is a database which keep files in a file system. If we want to save records there, it will save the records physically in its specific format. Later it will go there to read the records.

If we do this in docker, docker doesn't keep the state so next time the state will be lost. To make sure our data is in the database, we need to map a folder we have on our host machine to a folder in the container. This is called ***mounting***（挂载）.

So firts create a folder named `ny_taxi_postgres_data` in the same directory as `Dockerfile`. Then we will use volume to map this folder to the folder in the container.

```bash
docker run -it \
	-e POSTGRES_USER="root" \
	-e POSTGRES_PASSWORD="root" \
	-e POSTGRES_DB="ny_taxi" \
	-v /$(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
	-p 5433:5432 \
	postgres:13
```

There are two parts of configuration:

- environment variables:
  - `POSTGRES_USER`: username for logging into the database. Here we use `root`.
  - `POSTGRES_PASSWORD`: password for the database. Here we use `root`.
    - ***IMPORTANT: There values are only meant for testing. Please change them for any serious project.***
  - `POSTGRES_DB`: name of the database. Here we use `ny_taxi`.
- volume: `-v` points to the volume directory. The colon `:` separates the first part (path to the folder in the host computer) from the second part (path to the data folder inside the contain)
  - Path names must be **absolute** (full path). If you're a UNIX-like system, you can use `pwd` to print your local folder as a shortcut. This example should work with both `bash` and `zsh` shells.
  - This command will only work if run it from a directory which contains the `ny_taxi_postgres_data` subdirectory you created above.
- The `-p` is for post mapping. We map port `5433` on the host to port `5432` inside the Docker container. When you access port `5433` on the `host` machine, you are actually accessing port `5432` inside the Docker container, which is the port where the PostgreSQL database service running in the Docker container listens.
- The last argument is the image name and tag. We run the official `postgres` image on its version `13`.

We want to run a cli (command line interface) for accessing the database. Once the container is running, we can log into our database with [pgcli](https://www.pgcli.com/) using the following command:

```bash
pgcli -h localhost -p 5433 -u root -d ny_taxi
```

- `-h`: the host. Since we are running locally we can use `localhost`.
- `-p`: the port. The specified port number to connect to the PostgreSQL server is `5433`, which is the port mapped to the local host in the Docker command.
- `-u`: the username.
- `-d`: the database name.
- The password is not provided so it will be requested after running the command.

> Note: use the right port and make sure the container is running when you try to run the command, otherwise you will failed.

### Ingesting data to Postgres

We will now create a Jupyter Notebook `upload-data.ipynb` file which we will use to read a CSV file and export it to Postgres.

We will use data from the [NYC TLC Trip Record Data website](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page). Specifically, we will use the [Yellow taxi trip records CSV file for January 2021](https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2021-01.csv). A dictionary to understand each field is available [here](https://www1.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf).

> Note: knowledge of Jupyter Notebook, Python environment management and Pandas is asumed in these notes. Please check [this link](https://gist.github.com/ziritrion/9b80e47956adc0f20ecce209d494cd0a#pandas) for a Pandas cheatsheet and [this link](https://gist.github.com/ziritrion/8024025672ea92b8bdeb320d6015aa0d) for a Conda cheatsheet for Python environment management.

Check the completed `upload-data.ipynb` [in this link](../1_intro/upload-data.ipynb) for a detailed guide. Feel free to copy the file to your work directory; in the same directory you will need to have the CSV file linked above and the `ny_taxi_postgres_data` subdirectory.

To download the dataset, run the following command:

```bash
wget https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz
```

Then use the following command to unzip the file:

```bash
gzip -d yellow_tripdata_2021-01.csv.gz
```

To view the csv file:

```bash
less yellow_tripdata_2021-01.csv
```

Now, let's elaborate on the points covered in the notebook.

```bash
pd.io.sql.get_schema(df, name='yellow_taxi_data')
```

After storing CSV data in a DataFrame, we use `pd.io.sql.get_schema()` to convert the dataframe we have to a **DDL (Data Definition Language)** which is part of SQL to specify schemas. Here we also need to specify the name of the table.

> Note: SQL (Structured Query Language) is divided into the following categories:
>
> - ***DDL***: Data Definition Language.
>   * Define the database schema (create, modify, destroy)
>   * `CREATE`, `DROP`, `ALTER`, `TRUNCATE`, `COMMENT`, `RENAME`
> - ***DQL***: Data Query Language.
>   * Perform queries on the data within schema objects. Get data from the database and impose order upon it.
>   * `SELECT`
> - ***DML***: Data Manipulation Language.
>   * Manipulates data present in the database.
>   * `INSERT`, `UPDATE`, `DELETE`, `LOCK`...
> - ***DCL***: Data Control Language.
>   * Rights, permissions and other controls of the database system.
>   * Usually grouped with DML commands.
>   * `GRANT`, `REVOKE`
> - ***TCL***: Transaction Control Language.
>   * Transactions within the database.
>   * Not a universally considered category.
>   * `COMMIT`, `ROLLBACK`, `SAVEPOINT`, `SET TRANSACTION`

We're not sure if this statement is suitable for postgres, so we need to generate this DDL statement in something that postgres will understand. We need to connect to postgres and it will generate the statement that is specifically for postgres.

`Pandas` use a python library called `sqlalchemy` to allow developers to interact with relational databases using `Python`. The `create_engine` function is a tool for creating database engines, and it's an important component of SQLAlchemy.

`Psycopg2` is a PostgreSQL database adapter for Python that allows Python applications to interact with PostgreSQL databases.

Now we need to create an engine:

```bash
engine = create_engine('postgresql://root:root@localhost:5433/ny_taxi')
```

- `postgresql`: the type of the database.
- `root`: the user.
- `root`: the password.
- `localhost`: the host name.
- `5433`: the port.
- `ny_taxi`: the database name.

The purpose of this line of code is to create an engine object that connects to a PostgreSQL database named `ny_taxi`, using the username `root` and password `root`, on the localhost's port `5432`.

Now we need to specify the connection, using the engine that we just created:

```bash
pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine)
```

`con=engine` specifies that the engine object to connect to the database is `engine`, so the `get_schema()` function knows which database to create the table structure in.

```bash
df.to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')
```

Write the data from the dataframe into a database table named `yellow_taxi_data`, using the specified engine object for connection. If a table with the same name already exists in the database, it will be replaced it.

> Summary: `pgcli` is a command-line tool that allows you to interact directly with PostgreSQL databases in the terminal, while `SQLAlchemy` is a Python library that enables you to interact with databases using Python code.



## Connecting pgAdmin and Postgres

`pgcli` is a handy tool but it's cumbersome to use. `pgAdmin` is a web-based tool that makes it more convenient to access and manage databases. It's possible to run pgAdmin as container along with the Postgres container, but both containers should be in the same `virtual network` so that they can find each other.

Let's create a virtual Docker network called `pg-network`:

```bash
docker network create pg-network
```

> You can remove the network later with the command `docker network rm pg-network` . You can look at the existing networks with `docker network ls`.

Now re-run the Postgres container with the added network name and the container name, so that the pgAdmin container can find it (we use `pg-database` for the container name here):

```bash
docker run -it \
	-e POSTGRES_USER="root" \
	-e POSTGRES_PASSWORD="root" \
	-e POSTGRES_DB="ny_taxi" \
	-v /$(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
  -p 5433:5432 \
	--network=pg-network \
	--name pg-database \
  postgres:13
```

We will now run the pgAdmin container on another terminal:

```bash
docker run -it \
	-e PGADMIN_DEFAULT_EMAIL="admin@admin.com" \
	-e PGADMIN_DEFAULT_PASSWORD="root" \
	-p 8080:80 \
	--network=pg-network \
	--name pgadmin \
	dpage/pgadmin4
```

- The container needs 2 environment variables:
  - a login email
  - a password
- ***IMPORTANT: these are example values for testing and should never be used on production. Change the accordingly when needed.***
- `pgAdmin` is a web app and its default port is 80; we map it to 8080 in our localhost to avoid any possible conflicts.
- Name is less important for `pgAdmin` because `pgadmin` needs to connect to `postgres` but no one needs to connect to `pdAdmin`.
- The actual image name is `dpage/pgadmin4`.

After running the above 2 commands, we are able to load pgAdmin on web broswer by browsing to `localhost:8080`. Use the same email and password you use for running the container to log in.

![pgadmin](./image-01/pgadmin.png)

Then we register a new server using the following settings:

Under *General* give the Server a name and under *Connection* add the same host name, user and password you used when running the container.

<img src="./image-01/setting-pg.png" alt="setting-pg" style="zoom:100%;" />

After that we are able to view the data we have ingested:

![view_data](./image-01/view_data.png)

> One question: Why does the data in the postgres container not disappear after re-running it?



## Putting the ingestion script into Docker

We will now export the Jupyter notebook file to a regular python script and use Docker to run it.

### Exporting and testing the script

We can export the `ipynb` file to `py` with this command:

```bash
jupyter nbconvert --to=script upload-data.ipynb
```

Clean up the script by removing everything we don't need. We will also rename it to `ingest_data.py` and add a few modifications:

```py
#!/usr/bin/env python
# coding: utf-8

import os
import argparse

from time import time

import pandas as pd
from sqlalchemy import create_engine


def main(params):
    user = params.user
    password = params.password
    host = params.host 
    port = params.port 
    db = params.db
    table_name = params.table_name
    url = params.url
    
    # the backup files are gzipped, and it's important to keep the correct extension
    # for pandas to be able to open the file
    if url.endswith('.csv.gz'):
        csv_name = 'output.csv.gz'
    else:
        csv_name = 'output.csv'

    os.system(f"wget {url} -O {csv_name}")

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000)

    df = next(df_iter)

    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    df.to_sql(name=table_name, con=engine, if_exists='append')


    while True: 

        try:
            t_start = time()
            
            df = next(df_iter)

            df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
            df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

            df.to_sql(name=table_name, con=engine, if_exists='append')

            t_end = time()

            print('inserted another chunk, took %.3f second' % (t_end - t_start))

        except StopIteration:
            print("Finished ingesting data into the postgres database")
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingest CSV data to Postgres')

    parser.add_argument('--user', required=True, help='user name for postgres')
    parser.add_argument('--password', required=True, help='password for postgres')
    parser.add_argument('--host', required=True, help='host for postgres')
    parser.add_argument('--port', required=True, help='port for postgres')
    parser.add_argument('--db', required=True, help='database name for postgres')
    parser.add_argument('--table_name', required=True, help='name of the table where we will write the results to')
    parser.add_argument('--url', required=True, help='url of the csv file')

    args = parser.parse_args()

    main(args)
```

To configure it, we will use a library called `argparse` which allows us to parse command line arguments.

- Username
- Password
- Host
- Port
- Database name
- Table name
- URL for the data file

The engine we created for connecting to Postgres will be tweaked so that we pass the parameters to build the URL from them.

```python
engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
```

 In order to test the script we will have to drop the table we previously created. Run the following command in `pgAdmin`:

```postgresql
DROP TABLE yellow_taxi_data;
```

We are now ready to test the script with the following command:

```bash
python3 ingest_data.py \
	--user=root \
	--password=root \
	--host=localhost \
	--port=5433 \
	--db=ny_taxi \
	--table_name=yellow_taxi_trips \
	--url="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
```

- Now that we've changed the table name from `yellow_taxi_data` to `yellow_taxi_trips`.

Back in pgAdmin, refresh the Tables and check that `yellow_taxi_trips` was created. You can also run a SQL query to chech the contents:

```postgresql
SELECT
    COUNT(1)
FROM
    yellow_taxi_trips;
```

- The query should return 1,369,765 rows.

### Dockerizing the script

Let's modify the `Dockerfile` we created before to include our `ingest_data.py` script and create a new image.

```dockerfile
FROM python:3.9

# we need to install wget to download the csv file
RUN apt-get install wget

# sqlalchemy needs psycopg2
RUN pip install pandas sqlalchemy psycopg2

WORKDIR /app
COPY ingest_data.py ingest_data.py

ENTRYPOINT ["python", "ingest_data.py"]
```

Build the image:

```bash
docker build -t taxi_ingest:v001 .
```

- `-t`: specify the tag

And run it:

```bash
docker run -it \
	--network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_trips \
    --url="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
```

- We need to provide the network for `Docker` to fine the `Postgres` container. It goes before the name of the image.
- ***IMPORTANT: here we use `pg-database` as host. Since `Postgres` is running on a separate contianer, the host argument will have to point to the container name of `Postgres`.***
- You can drop the table in `pgAdmin` beforehand if you want, but the script will automatically replace the pre-existing table.

***Small tips:***

Instead of waiting for the file downloading from the URL, we can use something else. In previous steps we have already downloaded the CSV file.

In python there is something called `http.server`.

```bash
python -m http.server
```

Now we start a python http server:

<img src="./image-01/http-server.png" alt="http-server" style="zoom:50%;" />

Then we go to the server host: `localhost:8000`

![http-server-1](./image-01/http-server-1.png)

Copy the link of the data file and we can download the csv file pretty fast.

```http
http://localhost:8000/yellow_tripdata_2021-01.csv
```

One more thing we need to do is that we should replace the `localhost` with the `ip address` of our computer. You can use `ifconfig getifaddr en0` to get this.

> Note: if we use the csv file here, we should change the `os.system` code since we don't have to unzip the file.

### About the port

```bash
pgcli -h localhost -p 5433 -u root -d ny_taxi
```

- Here we use port `5433` to connect to `postgres`, that's because the PostgreSQL server is listening on port `5433` on the local host.

```python
engine = create_engine('postgresql://root:root@localhost:5433/ny_taxi')
```

- Here the port refers to the `5433` port on our machine, because we are trying to access the postgres from local host.

```bash
python3 ingest_data.py \
	--user=root \
	--password=root \
	--host=localhost \
	--port=5433 \
	--db=ny_taxi \
	--table_name=yellow_taxi_trips \
	--url="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
```

- Here we use port `5433`, the reason is same as the previous one.

```bash
docker run -it \
	--network=pg-network \
  taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pg-database \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_trips \
    --url="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
```

- Here we use `5432` because we are accessing the postgres database inside the container. The host is `pg-database` and it is listening on the port `5432`.

In summary, if we are connecting to portgres from localhost we should use port `5433`. And if we are sending requests to the `pg-database`, we should use its port `5432`. Here we just did local testing. In real life scenario we would use a URL to some database that runs in the cloud like `Bigquery`.



## Running Postgres and pgAdmin with Docker-Compose

`docker-compose` allows us to launch multiple containers using a single configuration file, so that we don't have to run multiple complex `docker run` commands separately.

Docker compose makes use of YAML files. Here's the `docker-compose.yaml` file for running the Postgres and pgAdmin containers:

```yaml
services:
  pgdatabase:
    image: postgres:13
    environment:
      - POSTGRES_USER=root
      - POSTGRES_PASSWORD=root
      - POSTGRES_DB=ny_taxi
    volumes:
      - "./ny_taxi_postgres_data:/var/lib/postgresql/data:rw"
    ports:
      - "5433:5432"
  pgadmin:
    image: dpage/pgadmin4
    environment:
      - PGADMIN_DEFAULT_EMAIL=admin@admin.com
      - PGADMIN_DEFAULT_PASSWORD=root
    ports:
      - "8080:80"
```

- We don't have to speficy a network because `docker-compose` takes care of it: every single container (or "service", as the file states) will run within the same network and will be able to find each other according to their names (`pgdatabase` and `pgadmin` in this example).

- All other details from the `docker run` commands (environment variables, volumes and ports) are mentioned accordingly in the file following YAML syntax.

We can now run Docker compose using the following command fron the same directory where `docker-compose.yaml` is found. Make sure that all previous containers aren't running anymore:

```bash
docker-compose up
```

> Note: this command asumes that the `ny_taxi_postgres_data` used for mounting the volume is in the same directory as `docker-compose.yaml`.

You will have to press `Ctrl+C` in order to shut down the containers. The proper way of shutting them down is with this command:

```bash
docker-compose down
```

And if you want to run the containers again in the background rather than in the foreground (thus freeing up your terminal), you can run them in detached mode:

```bash
docker-compose up -d
```

One problem is that we didn't see the data we ingested before in the `pgAdmin`. Why? 

We did not define a Network in the `docker-compose.yaml` file, therefore docker compose will create one for you which name is derived from the folder `docker-compose.yaml` is located in. Here it use the network `2_docker_sql_default`.

<img src="./image-01/docker-network.png" alt="docker-network" style="zoom:45%;" />

If you want to re-run the dockerized ingest script when you run Postgres and pgAdmin with `docker-compose`, you will have to find the name of the virtual network that Docker compose created for the containers. You can use the command `docker network ls` to find it and then change the `docker run` command for the dockerized script to include the network name.

```bash
docker run -it \
	--network=2_docker_sql_default \
  taxi_ingest:v001 \
		--user=root \
		--password=root \
		--host=pgdatabase \
		--port=5432 \
		--db=ny_taxi \
		--table_name=yellow_taxi_trips \
		--url="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
```

After running this, re-run command `docker-compose up`, you will be able to see the data in `pgAdmin`.



## SQL refresher

Now we use the following code to ingets the `Zones` data to the database.

```bash
wget https://s3.amazonaws.com/nyc-tlc/misc/taxi+_zone_lookup.csv
```

```python
df_zones = pd.read_csv('taxi+_zone_lookup.csv')
df_zones.to_sql(name='zones', con=engine, if_exists='replace')
```

The columns in `zones` are:

| LocationID | Borough | Zone           | service_zone |
| ---------- | ------- | -------------- | ------------ |
| 1          | EWR     | Newark Airport | EWR          |

The columns in `yellow_taxi-trips` are:

| VendorID | tpep_pickup_datetime | tpep_dropoff_datetime | passenger_count | trip_distance | RatecodeID | store_and_fwd_flag | PULocationID | DOLocationID | payment_type | fare_amount | extra | mta_tax | tip_amount | tolls_amount | improvement_surcharge | total_amount | congestion_surcharge |
| -------- | -------------------- | --------------------- | --------------- | ------------- | ---------- | ------------------ | ------------ | ------------ | ------------ | ----------- | ----- | ------- | ---------- | ------------ | --------------------- | ------------ | -------------------- |
| 1        | 2021-01-01 00:30:10  | 2021-01-01 00:36:12   | 1               | 2.10          | 1          | N                  | 142          | 43           | 2            | 8.0         | 3.0   | 0.5     | 0.00       | 0.0          | 0.3                   | 11.80        | 2.5                  |

- "VendorID": a code indicating the TPEP provider that provided the record.
- tpep_pickup_datetime: the date and time when the meter was enganed.

- tpep_dropoff_datetime: the date and time when the meter was disengaged.

- passenger_count: the number of passengers in the vehicle.

-  trip_distance: the elapsed trip distance in miles reported by the taximeter.

- "RatecodeID": the final rate code in effect at the end of the trip.

- store_and_fwd_flag: the flag indicates whether the trip record was held in vehicle memory before sending to the vendor.

- "PULocationID": pick up location id, TLC Taxi Zone in which the taximeter was engaged.

- "DOLocationID": drop off location id, TLC Taxi Zone in which the taximeter was engaged.

- payment_type: a numeric code signifying how the passengers paid for the trip.

- fare_amount: the time-and-distance fare calculated by the meter.

- extra: miscellaneous extras and surcharges. 

- mta_tax: $0.50 MTA tax that is automatically triggered based on the metered rate in use.

- tip_amount: $0.30 improvement surcharge assessed trips at the flag drop.

- tolls_amount: tip amount.

- improvement_surcharge: total amount of all tolls paid in trip. 

- total_amount: the total amount charged to passengers.

- congestion_surcharge: total amount collected in trip for NYS congestion surcharge.

***IMPORTANT: We use double quotes (`""`) for the column names because in Postgres we need to use them if the column names contains capital letters.***

Below are a series of SQL query examples to remember how SQL works. For this example we'll asume that we're working with 2 tables named `trips` (list of all yelow taxi trips of NYC for January 2021) and `zones` (list of zone IDs for pick ups and drop offs).

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    total_amount,
    CONCAT(zpu."Borough", '/', zpu."Zone") AS "pickup_loc",
    CONCAT(zdo."Borough", '/', zdo."Zone") AS "dropoff_loc"
FROM
    yellow_taxi_trips t,
    zones zpu,
    zones zdo
WHERE
    t."PULocationID" = zpu."LocationID" AND
    t."DOLocationID" = zdo."LocationID"
LIMIT 100;
```

- We make use of ***inner join*** to display combined info as a single column.
  - The new "vitrual" column `pickup_loc` contains the values of both `Borough` and `Zone` columns of the zones tables, separated by a slash (/).
  - Same for dropoff_loc.
- Here we want to get the location of the pick up and drop off.

- We give aliases to the trip and `zones` tables for `easier` access.

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    total_amount,
    CONCAT(zpu."Borough", '/', zpu."Zone") AS "pickup_loc",
    CONCAT(zdo."Borough", '/', zdo."Zone") AS "dropoff_loc"
FROM
    yellow_taxi_trips t JOIN zones zpu
        ON t."PULocationID" = zpu."LocationID"
    JOIN zones zdo
        ON t."DOLocationID" = zdo."LocationID"
LIMIT 100;
```

- Exactly the same statement as before but rewritten using explicit `JOIN` keywords.
  - Explicit inner joins are preferred over implicit innder joins.

- The `JOIN` keyword is used after the `FROM` statement rather than the `WHERE` statement. The `WHERE` statement is actually unneeded.

- You can also use the keyword `INNER JOIN` for clarity.

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    total_amount,
    "PULocationID",
    "DOLocationID"
FROM
    yellow_taxi_trips t
WHERE
    "PULocationID" is NULL
LIMIT 100;
```

- Select rows from the `yellow_taxi_trips` table whose pick up location is null and displays specific columns.
- If you have not modified the original tables, this query should return an empty list.

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    total_amount,
    "PULocationID",
    "DOLocationID"
FROM
    yellow_taxi_trips t
WHERE
    "DOLocationID" NOT IN (
        SELECT "LocationID" FROM zones
    )
LIMIT 100;
```

- Select rows fromn the `yellow_taxi_trips` table whose drop off location ID does not appear in the `zones` table.
- If you did not modify any rows in the original datasets, the query would return an empty list.

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    total_amount,
    CONCAT(zpu."Borough", '/', zpu."Zone") AS "pickup_loc",
    CONCAT(zdo."Borough", '/', zdo."Zone") AS "dropoff_loc"
FROM
    yellow_taxi_trips t LEFT JOIN zones zpu
        ON t."PULocationID" = zpu."LocationID"
    LEFT JOIN zones zdo
        ON t."DOLocationID" = zdo."LocationID"
LIMIT 100;
```

- Similar to the join query from before but we use a ***left join*** instead.
- ***Left joins*** shows all rows from the "left" part of the statement but only the rows from the "right" part that overlap with the "left" part.
- This join is useful if we deleted one of the `LocationID` rows The inner join would omit some rows from the `yellow_taxi_trips` table, but this query will show all rows. However, since one ID is missing, the "virtual" columns we defined to transform location ID's to actual names will appear with empty strings if the query cannot find the location ID.

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    DATE_TRUNC('DAY', tpep_pickup_datetime),
    total_amount
FROM
    yellow_taxi_trips t
LIMIT 100;
```

- Select all rows from the `yellow_taxi_trips` table but displays specific columns.
- `DATE_TRUNC` is a function that truncates a timestamp. When using `DAY` as a parameter, it removes any smaller values (hours, minutes, seconds) and displays them as `00:00:00` instead.

```postgresql
SELECT
    tpep_pickup_datetime,
    tpep_dropoff_datetime,
    CAST(tpep_pickup_datetime AS DATE) as "day",
    total_amount,
FROM
    yellow_taxi_trips t
LIMIT 100;
```

- `CAST(expression AS data_type)`
- Very similar to previous query, but instead it casts the `TIMESTAMP` type to `DATE`, so that the hours:minutes:seconds info is completely omitted rather than show as `00:00:00`. The columns will be displayed under the name `day`.

```postgresql
SELECT
    CAST(tpep_pickup_datetime AS DATE) as "day",
    COUNT(1)
FROM
    yellow_taxi_trips t
GROUP BY
    CAST(tpep_pickup_datetime AS DATE)
ORDER BY "day" ASC;
```

* Counts the amount of records in the `yellow_taxi_trips` table grouped by day.
* We remove the limit of 100 records because we do not want to restrict the amount of info on screen.
* Grouping does not guarantee order, so we enforce that the rows will be displayed in ascending order from earliest to latest day.

```postgresql
SELECT
    CAST(tpep_pickup_datetime AS DATE) as "day",
    COUNT(1) as "count",
    MAX(total_amount),
    MAX(passenger_count)
FROM
    yellow_taxi_trips t
GROUP BY
    CAST(tpep_pickup_datetime AS DATE)
ORDER BY "count" DESC;
```

* Similar to the previous query but orders the rows by count and displays them in descending order, so that the day with the highest amount of trips is shown first.
* We also show the maximum amount that a driver earned in a trip for that day and the maximum passenger count on a single trip for that day.

```postgresql
SELECT
    CAST(tpep_pickup_datetime AS DATE) as "day",
    "DOLocationID",
    COUNT(1) as "count",
    MAX(total_amount),
    MAX(passenger_count)
FROM
    yellow_taxi_trips t
GROUP BY
    1, 2
ORDER BY "count" DESC;
```

- Similar to previous but we also include the drop off location column and we group by it as well, so that each row contains the amount of trips for that location by day.
- Instead of having to repeat the same line in both the `SELECT` and `GROUP BY` parts, we can simply indicate the arguments we use after the `SELECT` keyword by order number.
  * SQL is 1-indexed. The first argument is 1, not 0.

```postgresql
SELECT
    CAST(tpep_pickup_datetime AS DATE) as "day",
    "DOLocationID",
    COUNT(1) as "count",
    MAX(total_amount),
    MAX(passenger_count)
FROM
    yellow_taxi_trips t
GROUP BY
    1, 2
ORDER BY
    "day" ASC,
    "DOLocationID" ASC;
```

- Similar to previous query but we now order by ascending order both by day and then drop off location ID, both in ascending order.



# Google Cloud Platform

## Introduction to GCP

What is it?

- Cloud computing services offered by google.
- Includes a range of hosted services for compute, storage and application development that run on Google hardware.
- Same hardware on which google runs its service.

<img src="./image-01/GCP.png" alt="GCP" style="zoom:50%;" />

## GCP setup

GCP is organized around _projects_. You may create a project and access all available GCP resources and services from the project dashboard.

### Initial setup

GCP is organized around _projects_. You may create a project and access all available GCP resources and services from the project dashboard.

We will now create a project and a _service account_, and we will download the authentication keys to our computer. A _service account_ is like a user account but for apps and workloads; you may authorize or limit what resources are available to your apps with service accounts.

Please follow these steps:

1. Create an account on GCP. You should receive $300 in credit when signing up on GCP for the first time with an account.

1. Setup a new project and write down the Project ID.

   1. From the GCP Dashboard, click on the drop down menu next to the _Google Cloud Platform_ title to show the project list and click on _New project_.
   1. Give the project a name. We will use `dtc-de` in this example. You can use the autogenerated Project ID (this ID must be unique to all of GCP, not just your account). Leave the organization as _No organization_. Click on _Create_.
   1. Back on the dashboard, make sure that your project is selected. Click on the previous drop down menu to select it otherwise.

1. Setup a service account for this project and download the JSON authentication key files.

   1. _IAM & Admin_ > _Service accounts_ > _Create service account_
      - Service account: is an entity used in the Google Cloud Platform (GCP) to identify applications and services interacting with GCP APIs. It has a unique email address and is endowed with specific permissions to access GCP resources. You won't need your owner's account or the admin account for the resources to interact with each other. It has restricted or limited permissions.
   1. Provide a service account name. We will use `dtc-de-user`. Leave all other fields with the default values. Click on _Create and continue_.
   1. Grant the Viewer role (_Basic_ > _Viewer_) to the service account and click on _Continue_
   1. There is no need to grant users access to this service account at the moment. Click on _Done_.
   1. With the service account created, click on the 3 dots below _Actions_ and select _Manage keys_.
   1. _Add key_ > _Create new key_. Select _JSON_ and click _Create_. The files will be downloaded to your computer. Save them to a folder and write down the path.

1. Download the [GCP SDK](https://cloud.google.com/sdk/docs/quickstart) for local setup. Follow the instructions to install and connect to your account and project.

1. Set the environment variable to point to the auth keys.

   1. The environment variable name is `GOOGLE_APPLICATION_CREDENTIALS`

   1. The value for the variable is the path to the json authentication file you downloaded previously.

   1. Check how to assign environment variables in your system and shell. In bash, the command should be:

      ```bash
      export GOOGLE_APPLICATION_CREDENTIALS="<path/to/authkeys>.json"
      ```

   1. Refresh the token and verify the authentication with the GCP SDK:

      ```bash
      gcloud auth application-default login
      ```

You should now be ready to work with GCP.

### Setup for access

In the following chapters we will setup a _Data Lake_ on Google Cloud Storage and a _Data Warehouse_ in BigQuery. We will explore these concepts in future lessons but a Data Lake is where we would usually store data and a Data Warehouse provides a more structured way to access this data.

We need to setup access first by assigning the Storage Admin, Storage Object Admin, BigQuery Admin and Viewer IAM roles to the Service Account, and then enable the `iam` and `iamcredentials` APIs for our project.

Please follow these steps:

1. Assign the following IAM Roles to the Service Account: Storage Admin, Storage Object Admin, BigQuery Admin and Viewer.
   1. On the GCP Project dashboard, go to _IAM & Admin_ > _IAM_
   1. Select the previously created Service Account and edit the permissions by clicking on the pencil shaped icon on the left.
   1. Add the following roles and click on _Save_ afterwards:
      * `Storage Admin`: for creating and managing _buckets_.
      * `Storage Object Admin`: for creating and managing _objects_ within the buckets.
      * `BigQuery Admin`: for managing BigQuery resources and data.
      * `Compute Admin`: for managing computing resources.
      * `Viewer` should already be present as a role.
1. Enable APIs for the project (these are needed so that Terraform can interact with GCP):
   * https://console.cloud.google.com/apis/library/iam.googleapis.com
   * https://console.cloud.google.com/apis/library/iamcredentials.googleapis.com
1. Make sure that the `GOOGLE_APPLICATION_CREDENTIALS` environment variable is set.



## Terraform

### Introduction to Terraform

1. What if Terraform?
   - open-source tool by HashiCorp, used for provisioning infrastructure resources
   - supports DevOps best practices for change management
   - Managing configuration files in source control to maintain an ideal provisioning state for testing and production environments.
2. What is IaC?
   - Infrastructue-as-Code
   - build, change, and manage your infrastructure in a safe, consistent, and repeatable way by defining resource configurations that you can version, reuse and share (kind of like a git version control but for infrastructure)
3. Some advantages
   - Infrastructure lifecycle management
   - Version control commits, easier collaboration
   - Very useful for stack-based deployments, and with cloud providers such as AWS, GCP, Azue, K8S...
   - State-based approach to track resource changes throughout deployments
   - Reproducibility
   - Ensure resources are removed
4. What Terraform is not?
   - Does not manage and update code on infrastructure
   - Does not give you the ability to change immutable resources
   - Not used to manage resources not defined in your terraform files
5. What are providers?
   - Code that allows terraform to communicate to manage resources on
     - AWS
     - Azure
     - GCP
     - Kubernetes
     - VSphere
     - Alibaba Cloud
     - Oracle Cloud Infrastruture

[Terraform](https://www.terraform.io/) is an [infrastructure as code](https://www.wikiwand.com/en/Infrastructure_as_code) tool that allows us to provision infrastructure resources as code, thus making it possible to handle infrastructure as an additional software component and take advantage of tools such as version control. It also allows us to bypass the cloud vendor GUIs. In other words, terraform lets us define both cloud and on-prem resources in human-readable configuation files that you can version, reuse and share. You can then use a consistent workflow to provision and manage all your infrastructure throughout its lifecycle.

### Terraform Basics

There are 2 important components to Terraform: the code files and Terraform commands.

The set of files used to describe infrastructure in Terraform is known as a Terraform ***configuration***. Terraform configuration files end up in `.tf` for files wtritten in Terraform language or `tf.json` for JSON files. A Terraform configuration must be in its own working directory; you cannot have 2 or more separate configurations in the same folder.

And here are some useful commands of Terraform:

- `terraform init`: get the provider we need, download the necessary plugins to connect to the GCP and download the ro `./.terraform`.
- `terraform plan`: see what we are about to do. The infrastructure plan will be printed on screen with all the planned changes marked with a `+` sign next to them.
- `terraform apply`: do what is in the `tf` file. You need to confirm this step by typing `yes` when prompted. This will create all the necessary components in the infrastructure and return a `terraform.tfstate` with the current state of the infrastructure.
- `terraform destroy`: remove everything defined in the `tf` files. You may destroy the infrastructure so that is doesn't consume credit unnecessarily. You will have to confirm this step by typing `yes` when prompted. This will remove your complete stack from the cloud.
- `terraform fmt`: code formatting.

Let's create a `terraform` directory and open it in vscode. Here we install the `terraform` extension. Then create a basic  `main.tf` written in Terraform language with all of the necessary info to describe basic infrastructure  (google 'terraform google provider' for more instructions).

> Note: one useful tip here, if you don't want to do code formatting manually, you can run this command in terminal: `terraform fmt`. This command will do code formatting for you.

```java
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.13.0"
    }
  }
}

provider "google" {
  project = "<your-project-id>"
  region  = "us-central1"
}

resource "google_compute_network" "vpc_network" {
  name = "terraform-network"
}
```

* Terraform divides information into ***blocks***, which are defined within braces (`{}`), similar to Java or C++. However, unlike these languages, statements are not required to end with a semicolon `;` but use linebreaks instead.
* By convention, arguments with single-line values in the same nesting level have their equal signs (`=`) aligned for easier reading.
* There are 3 main blocks: `terraform`, `provider` and `resource`. There must only be a single `terraform` block but there may be multiple `provider` and `resource` blocks.
* The `terraform` block contains settings:
  * The `required_providers` sub-block specifies the providers required by the configuration. In this example there's only a single provider which we've called `google`.
    * A _provider_ is a plugin that Terraform uses to create and manage resources.
    * Each provider needs a `source` in order to install the right plugin. By default the Hashicorp repository is used, in a similar way to Docker images.
      * `hashicorp/google` is short for `registry.terraform.io/hashicorp/google` .
    * Optionally, a provider can have an enforced `version`. If this is not specified the latest version will be used by default, which could introduce breaking changes in some rare cases.
  * We'll see other settings to use in this block later.
* The `provider` block configures a specific provider. Since we only have a single provider, there's only a single `provider` block for the `google` provider.
  * The contents of a provider block are provider-specific. The contents in this example are meant for GCP but may be different for AWS or Azure.
  * Some of the variables seen in this example, such as `credentials` or `zone`, can be provided by other means which we'll cover later.
* The `resource` blocks define the actual components of our infrastructure. In this example we have a single resource.
  * `resource` blocks have 2 strings before the block: the resource ***type*** and the resource ***name***. Together the create the _resource ID_ in the shape of `type.name`.
  * About resource types:
    * The first prefix of the resource type maps to the name of the provider. For example, the resource type `google_compute_network` has the prefix `google` and thus maps to the provider `google`.
    * The resource types are defined in the Terraform documentation and refer to resources that cloud providers offer. In our example [`google_compute_network` (Terraform documentation link)](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/compute_network) refers to GCP's [Virtual Private Cloud service](https://cloud.google.com/vpc).
  * Resource names are the internal names that we use in our Terraform configurations to refer to each resource and have no impact on the actual infrastructure.
  * The contents of a resource block are specific to the resource type. [Check the Terraform docs](https://registry.terraform.io/browse/providers) to see a list of resource types by provider.
    * In this example, the `google_compute_network` resource type has a single mandatory argument called `name`, which is the name that the resource will have within GCP's infrastructure.
      * Do not confuse the _resource name_ with the _`name`_ argument!

Then run it:

```bash
terraform init
```

> Note: you can kind of think that provider let us go to the door and the credential file is the key that let us open the door.

Now let's create a bucket. Click [here](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket) for more instructions.

```java
resource "google_storage_bucket" "demo-bucket" {
  name          = "<your unique bucket name>"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}
```

Then run the following command to deploy it :

```bash
terraform plan
terraform apply
```

Now we can see the bucket has been created.

### Deployment with a Variables File

Let's use a Bigquery dataset. Check the [doc](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset) here for more instructions. Add the follwing configuration to the `main.tf` file:

```java
resource "google_bigquery_dataset" "dataset" {
  dataset_id = "demo_dataset"
}
```

Now the `main.tf` file should look like this:

```java
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.13.0"
    }
  }
}

provider "google" {
  project = "<Your project id>"
  region  = "us-central1"
}

resource "google_storage_bucket" "demo-bucket" {
  name          = "<Your unique bucket name>"
  location      = "US"
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "dataset" {
  dataset_id = "demo_dataset"
}
```

Now we can run `terraform apply` to deploy these resources. The output is like:

```bash
google_bigquery_dataset.dataset: Creating...
google_storage_bucket.demo-bucket: Creating...
google_bigquery_dataset.dataset: Creation complete after 1s [id=projects/<your project id>/datasets/demo_dataset]
google_storage_bucket.demo-bucket: Creation complete after 2s [id=<your project id>-terra-bucket]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

Go to the `Bigquery Studio` module and click on our project, we are able to see our `demo_dataset` there.

> Note: don't forget to run `terraform destroy` before going ahead.

Let's go ahead and create a new file called `variables.tf`.

```java
variable "project" {
  description = "Project"
  default     = "<Your project id>"
}

variable "region" {
  description = "Region"
  default     = "us-central1"
}

variable "location" {
  description = "Project Location"
  default     = "US"
}

variable "bq_dataset_name" {
  description = "My BigQuery Dataset Name"
  default     = "demo_dataset"
}

variable "gcs_bucket_name" {
  description = "My Storage Bucket Name"
  default     = "<Your project id>-terra-bucket"
}

variable "gcs_storage_class" {
  description = "Bucket Storage Class"
  default     = "STANDARD"
}
```

In the `variables.tf` we will store variables that may change depending on your needs and location. The ones to note are:

* `region` may vary depending on your geographical location; change it according to your needs.
* `bq_dataset_name` has the name of the table for BigQuery. You may leave it as it is or change it t fit your needs.
* `project` is the Project ID of your project in GCP. Since the ID is unique, it is good practice to have Terraform as for it every time in case the same code is applied on different projects.

And now the `main.tf` file looks like:

```java
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.13.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

resource "google_storage_bucket" "demo-bucket" {
  name          = var.gcs_bucket_name
  location      = var.location
  force_destroy = true

  lifecycle_rule {
    condition {
      age = 1
    }
    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = var.bq_dataset_name
  location   = var.location
}
```

You can definitely see that we replace the value of variables like `location` with the `var` we defined in the `variables.tf` file. Just one more thing to mention:

```java
resource "google_bigquery_dataset" "demo_dataset" {
  dataset_id = var.bq_dataset_name
  location   = var.location
}
```

- `google_bigquery_dataset`: the ***reource type*** in Terraform. It specifies that we are creating a resource related to Google BigQuery dataset. Terraform uses this to understand which provider and resource type it need to manage.
- `demo_dataset`: the ***local name*** given to the resource. It's like an identifier used within the Terraform configuration file to reference this specific resource. You can think of it as a variable name within Terraform.
- `dataset_id`: the ***ID*** of the BigQuery dataset. The dataset ID is a unique identifier for the dataset within a project. It's what you use to reference the dataset when quering or working with it.
  - ***IMPORTANT: `demo_dataset` is the local name defined for the resource in the Terraform configuration file, whereas `dataset_id` is an attribute of the Google BigQuery dataset resource, representing the identifier for the dataset to be created.***
- `location`: the ***location*** where the BigQuery dataset will be created. GCP organizes recources into regions and zones to optimize for performance, reliability and cost.

Run the following commands and we will see the `demo_dataset` being created.

```bash
terraform plan
terraform apply
```

Instead of using `export GOOGLE_APPLICATION_CREDENTIALS="<path/to/authkeys>.json"` to set the credential, we can make use of variables to do this.

```java
variable "credentials" {
  description = "My Credentials"
  default     = "<Path to your credential json file>"
}
```

And in `main.tf` file:

```java
provider "google" {
  credentials = file(var.credentials)
  project     = var.project
  region      = var.region
}
```



## GCP Cloud VM

Now we are in our project: 

Go to the *Compute Engine* > *VM instantces*:

- Generate an `SSH key` before creating an instance (click [here](https://cloud.google.com/compute/docs/connect/create-ssh-keys?hl=zh-cn) for more info):  

  ```bash
  ssh-keygen -t rsa -f ~/.ssh/gcp -C lbw -b 2048
  ```

  Now we have the `gcp` (private key) file and `gcp.pub` (public key) file in the `ssh` directory.

- Put the public key to the google cloud:

  - go to *Compute Engine* > *Metadata* > *SSH keys* > *Add SSH key*
  - run `cat gcp.pub` and copy the key to google cloud, click *Save*

- Go to *VM instances* > *Create instance*:

  - specify serveral fields:
    - Name: de-zoomcamp
    - Region: europe-west4 (Netherlands)
    - Zone: choose one
    - Preset: e2-standard-4 (4 vCPU, 2 core, 16 GB memory)
    - Boot disk: ubuntu 20.04 LTS, 30GB

- Now we create an instance and get the `External IP`. Run the following command in terminal to connect to the VM:

  ```bash
  ssh -i ~/.ssh/<your ssh private key> <you username>@<your external ip>
  ```

  You can run `htop` to check the type of VM.

- We already have `Google Cloud SDK`, and now we should configure this instance:

  - download `anaconda`: 

    ```bash
    wget https://repo.anaconda.com/archive/Anaconda3-2023.09-0-Linux-x86_64.sh
    bash Anaconda3-2023.09-0-Linux-x86_64.sh
    ```

    follow the instructions to download it.

  - We can configure the log in to the VM:

    ```bash
    cd .ssh/
    touch config
    vm config
    ```

    And write the following contents:

    ```json
    Host de-zoomcamp
        HostName <your external ip>
        User <your user name>
        IdentityFile <absolute path to private key>
    ```

    Run the following commands:

    ```bash
    cd
    ssh de-zoomcamp
    ```

    Now we are able to login to the VM. This is another implementation of:

    ```bash
    ssh -i ~/.ssh/<your ssh private key> <you username>@<your external ip>
    ```

  - After installed the anaconda, we use `ctrl+d` to log out, and use `ssh de-zoomcamp` to log in again. Now we can see the terminal changed from `<your username>@de-zoomcamp` to `(base) <your username>@de-zoomcamp`. And this indecates that anaconda works.

    If you don't want to log out and log in, you can run `source .bashrc` to activate anaconda.

  - Install docker:

    ```bash
    sudo apt-get update
    sudo apt-get install docker.io
    ```

  - Clone the course repo:

    ```bash
    git clone https://github.com/DataTalksClub/data-engineering-zoomcamp.git
    ```

    Choose `HTTPS` instead of `SSH` because it's an anonymous way to check the repo, otherwise you will need to `ssh` to github.

  - Give permissions to docker (click [here](https://github.com/sindresorhus/guides/blob/main/docker-without-sudo.md) for more info):

    ```bash
    sudo groupadd docker
    sudo gpasswd -a $USER docker
    sudo service docker restart
    ```

    Log out and log back, now we are able to run:

    ```bash
    docker run hello-world
    ```

  - Install docker compose:

    ```bash
    mkdir bin # where all the executable files exists
    cd bin/
    wget https://github.com/docker/compose/releases/download/v2.24.3/docker-compose-linux-x86_64 -O docker-compose # -O specify the output
    chmod +x docker-compose # change mode, add execute permission to make it executable
    ./docker-compose version
    ```

    Now we don't want to do this every time from the `bin` directory, and we want to make it visible from any directory. For that we need to edit this to the path variable.

    Run it:

    ```bash
    cd # cd to the home directory
    nano .bashrc
    ```

    Go to the end and add these contents:

    ```json
    export PATH="${HOME}/bin:${PATH}"
    ```

    `ctrl+o` > `enter` > `ctrl+x`

    ```bash
    source .bashrc
    docker-compose version
    ```

    We have `docker-compose.yaml` in our course project, you can go to the directory and run the command:

    ```bash
    docker-compose up -d
    ```

  - Install `pgcli`：

    ```bash
    pip install pgcli
    ```



## Docker Networking and Port Mapping

The general structure is as follows

HOST (Ubuntu)

- same default network

  - Postgres
    - port: 5432

  - pgAdmin
    - port: 80

- host machine
  - ports: 5433, 8080