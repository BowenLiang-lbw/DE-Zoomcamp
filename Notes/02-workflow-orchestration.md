[toc]

# Workflow Orchestration

## Data Lake

### What is a data lake?

A ***Data Lake*** is a central repository that holds *big data* from many sources.

The *data* in a Data Lake could either be structured, unstructured or a mix of both.

The main goal behind a Data Lake is being able to ingest data as quickly as possible and making it available to the other team members.

A Data Lake should be:

- Stores, secures and protects data at unlimited scale
- Able to run on inexpensive hardware
- Ingest structured and unstructured data
- Catalogs and indexes for analysis without data movement
- Connects data with analytics and machine learning tools

### Data Lake vs Data Warehouse

A ***Data Lake (DL)*** is not to be confused with a ***Data Warehouse (DW)***. There are several differences:

- Data Processing:
  - DL: The data is *raw* and has undergone minimal processing. The data is generally *unstructured*.
  - DW: The data is *refined*; it has been cleaned, pre-processed and *structured* for specific use cases.
- Size:
  - DL: Data Lakes are *large* and contains vast amounts of data, in the order of petabytes. Data is transformed when in use only and can be stored indefinitely.
  - DW: Data Warehouese are *small* in comparison with DLs. Data is always preprocessed before ingestion and may be purged periodically.
- Nature:
  - DL: data is *undefined* and can be used for a wide variety of purposes.
  - DW: data is historic and relational, such as transaction system, etc.
- Users:
  - DL: Data scientists, data analyst.
  - DW: Business analysts.
- Use case:
  - DL: Stream processing, machine learning, real-time analytics...
  - DW: Batch processing, business intelligence, reporting.

Data Lakes came into existence because as companies started to realize the importance of data, they soon found out that they couldn't ingest data right away into their DWs but they didn't want to waste uncollected data when their devs hadn't yet finished developing the necessary relationships for a DW, so the Data Lake was born to collect any potentially useful data that could later be used in later steps from the very start of any new projects.

### ETL vs ELT

When ingesting data, DWs use the ***Extract, Transform and Load*** (ETL) model whereas DLs use ***Extract, Load and Transform*** (ELT).

The main difference between them is the order of steps. In DWs, ETL (Schema on Write) means the data is _transformed_ (preprocessed, etc) before arriving to its final destination, whereas in DLs, ELT (Schema on read) the data is directly stored without any transformations and any schemas are derived when reading the data from the DL.

**Architecture**

- Extract: pull data from a source (API-NYC taxi dataset)
- Transform: Data cleaning, transformation, and partitioning
- Load: API to Mage, Mage to Postgres, GCS, BigQuery

### Data Swamp - Data Lakes gone wrong

Data Lakes are only useful if data can be easily processed from it. Techniques such as versioning and metadata are very helpful in helping manage a Data Lake. A Data Lake risks degenerating into a ***Data Swamp*** if no such measures are taken, which can lead to:

- No versioning of the data
- Incompatible schemes of the same data
- No metadata associated
- Joins between different datasets are not possible

### Data Lake Cloud Providers

- Google Cloud Platform > Cloud Storage
- Amazon Web Services > Amazon S3
- Microsoft Azure > Azure Blob Storage

## Intro to Orchestration

We will talk about ***orchestration*** this week and that is how you can orchestrate you data workflows using ***Mage*** and ***Ariflow***.

In the previous lesson we saw the definition of *data pipeline* and we created a *pipeline script* that downloaded a CSV and processed it so that we could ingest it to Postgres.

The script we created is an example of how **WE SHOULD NOT** create a pipeline, because it contains 2 steps whichi could otherwise be separated (downloading and processing). The reason is that if our internet connection is slow or if we're simply testing the script, it will have to download the CSV file every single time that we run the script, which is less than ideal. We should add some retry mechanism

Ideally, each of these steps would be contained as separate entities, like for example 2 separate scripts. For our pipeline, that would look like this:

```
(web) → DOWNLOAD → (csv) → INGEST → (Postgres)
```

We have now separated our pipeline into a `DOWNLOAD` script and a `INGEST` script.

In this lesson we will create a more complex pipeline:

```
(web)
  ↓
DOWNLOAD
  ↓
(csv)
  ↓
PARQUETIZE
  ↓
(parquet) ------→ UPLOAD TO S3
  ↓
UPLOAD TO GCS
  ↓
(parquet in GCS)
  ↓
UPLOAD TO BIGQUERY
  ↓
(table in BQ)
```

_Parquet_ is a [columnar storage datafile format](https://parquet.apache.org/) which is more efficient than CSV.

This ***Data Workflow*** has more steps and even branches. This type of workflow is often called a ***Directed Acyclic Graph*** (DAG) because it lacks any loops and the data flow is well defined.

The steps in capital letters are our ***jobs*** and the objects in between are the jobs' outputs, which behave as ***dependencies*** for other jobs. Each job may have its own set of ***parameters*** and there may also be global parameters which are the same for all of the jobs.

A ***Workflow Orchestration Tool*** allows us to define data workflows and parametrize them; it also provides additional tools such as history and logging.

The tools we will focus on in this course are **[Apache Airflow](https://airflow.apache.org/)** and [**Mage**](https://www.mage.ai/), but there are many others such as Luigi, Prefect, Argo, etc.

#### What is orchestration?

A large part of data engineering is **extracting**, **transforming**, and **loading** data between sources.

**Orchestration** is a process of **dependency management**, facilitated through **automation** (key piece, minimize manual work).

The data orchestrator manages scheduling, triggering, monitoring and even resource allocation for your data engineering workflows.

Every workflow requires sequential steps. Poorly squenced transformations brew a storm far more bitter.

- steps = tasks
- workflows = DAGs(directed acyclic graphs)

![de-lifecycle](./image-02/de-lifecycle.png)

#### What does a good solution look like?

A good orchestrator ***handles***:

- workflow management: define schedule, manage workflows efficiently, ensure tasks are executed in the right order, manage dependencies 
- automation: automate as much as possible
- error handling: come-up with built in solutions for handling errors, conditional logic branching and retrying failed tasks
- recovery: things are going break and we might lose data, there needs to be a way to backfill missing data and recover lost data
- monitoring and alerting: if a pipeline fails or if those retries do happen, it will send us notification
- resource optmization: optimize the best route for job execution
- observability: help manage the entire process from start to finish, ideally come with built-in observability functionality
- debugging: a part of observability, debug the pipeline
- compliance/auditing: 

A good orchestrator ***prioritizes***:

The developer experience:

- flow state: "I need to switch between 7 tools/services."
- feedback loops: "I spent 5 hours locally testing this DAG."
- Cognitive load: "How much do you need to know to do your job?"



## Intro to Airflow

### Airflow architecture

A typical Airflow installation consists of the following components:

<img src="https://airflow.apache.org/docs/apache-airflow/2.0.1/_images/arch-diag-basic.png" alt="airflow_architecture" style="zoom:67%;" />

- The **scheduler** is responsible for scheduling jobs. It handles both triggering scheduled workflow as well as submitting tasks to the executor to run. Monitors all tasks and DAGs and triggers the task instances once their dependencies are complete.
- The **executor** handles running tasks. In a default installation, the executor runs everything inside the scheduler but most production-suitable executors push task execution out to workers.
- A **worker** simply executes tasks given by the scheduler.
- A **webserver** which serves as the GUI to inspect trigger and debug DAGs and tasks. Available on `localhost:8080`.
- A **DAG directory** which is a folder with DAG files which is read by the scheduler and the executor (an by extension by any worker the executor might have).
- A **metadata database** (Postgres) used by the scheduler, the executor and the web server to store state. The backend of Airflow.
- Additional components (not shown in the diagram):
  - `redis`: a message broker that forwards messages from the scheduler to workers.
  - `flower`: app for monitoring the environment, available at port `5555` by default.
  - `airflow-init`: initialization service which we will customize for our needs. Initializes the configuration such as backend, user credentials, environment variables etc.

Airflow will create a folder structure when running:

- `./dags` - `DAG_FOLDER` for DAG files
- `./logs` - contains logs from task execution and scheduler.
- `./plugins` - for custom plugins

Additional definitions:

- `DAG`: Directed acyclic graph, specifies the dependencies between a set of tasks with explicit execution order, and has a beginning as well as an end. (Hence, “acyclic”). A _DAG's Structure_ is as follows:
  * DAG Definition
  * Tasks (eg. Operators)
  * Task Dependencies (control flow: `>>` or `<<` )  
- ***Task***: a defined unit of work. The Tasks themselves describe what to do, be it fetching data, running analysis, triggering other systems, or more. Common Types of tasks are:
  * ***Operators*** (used in this workshop) are predefined tasks. They're the most common.
  * ***Sensors*** are a subclass of operator which wait for external events to happen.
  * ***TaskFlow decorators*** (subclasses of Airflow's BaseOperator) are custom Python functions packaged as tasks.
- ***DAG Run***: individual execution/run of a DAG. A run may be scheduled or triggered.
- ***Task Instance***: an individual run of a single task. Task instances also have an indicative state, which could be `running`, `success`, `failed`, `skipped`, `up for retry`, etc.
  * Ideally, a task should flow from `none`, to `scheduled`, to `queued`, to `running`, and finally to `success`.

### Setting up Airflow with Docker

#### Pre-requisites

1. Rename your gcp-service-accounts-credentials file to `google_credentials.json` & store it in your `$HOME` directory.

   ```bash
   cd ~ && mkdir -p ~/.google/credentials/
   mv <path/to/your/service-account-authkeys>.json ~/.google/credentials/google_credentials.json
   ```

2. Ensure that your docker-compose version is v2.x or higher. And set the memory for your Docker Engine to minimum 5GB (ideally 8GB). If enough memory is not allocated, it might lead to airflow-webserver continuously restarting. On  Docker Desktop this can be changed in *Preferences* > *Resources*.

#### Setup (full version)

Please follow these instructions for deploying the "full" Airflow with Docker. Instructions for a "lite" version are provided in the next section but you must follow these steps first.

1. Create a new `airflow` subdirectory in your work directory.

2. Download the official Docker-compose YAML file for the latest Airflow version.

   ```bash
   curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.2.3/docker-compose.yaml'
   ```

   - The official `docker-compose.yaml` file is quite complex and contains [several service definitions](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#docker-compose-yaml).

3. We now need to set up the Airflow user. For MacOS, create a new `.env` in the same folder as the `docker-compose.yaml` file with the content below:

   ```bash
   AIRFLOW_UID=50000
   ```

   Configure them for the docker-compose:

   ```bash
   mkdir -p ./dags ./logs ./plugins
   echo -e "AIRFLOW_UID=$(id -u)" > .env
   ```

4. The base Airflow Docker image won't work with GCP, so we need to customize it to suit our needs. 

## Intro to Mage

### What is Mage?

***Mage*** is an open-source pipeline tool for orchestrating, transforming, and integrating (like "Five Tran" or "Airbyte", taking data from one source and send it to another) data. Mage has an exclusive data integration functionality that's sort of separate from the rest of the tool.

The entire experience is kind of just designed to minimize cognitive load, improve the ability to iterate quickly on pipelines and build data workflows that have software engineering best practices in mind.

Main concepts:

<img src="./image-02/Mage-1.png" alt="Mage-1" style="zoom:50%;" />

- `Project`: 
  - home base, within each project you can have multiple projects in an instance.
  - a project forms the basis for all the work you can do in Mage (like a Github repo).
  - it contains the code for all of your pipelines, blocks, and other assets.
  - A Mage instance has one or more projects.
- `Pipeline`: 
  - within each project there are pipelines which are like DAGs or data workflows.
  - a pipeline is a workflow that executes some data operation, maybe extracting, transforming, and loading data from an API. They're also called DAGs on other platforms.
  - in Mage, pipelines can contain *Blocks* (written in SQL, Python, or R) and charts.
  - Each pipeline is represented by a YAML file in the "pipelines" folder of your project.
- `Blocks`: 
  - each pipeline is composed of blocks and blocks are the atomic units that make up a transformation in Mage. Commonly we use block to export, transform or load data.
  - A block is a file that can be executed independently or within a pipeline.
  - blocks from Directed Acyclic Graphs (DAGs), which we call pipelines.
  - A block won't start running in a pipeline until all its upstreams dependencies are met.
  - Changing one block will change it everywhere it's used, but it's easy to detach blocks to seperate instances of necessary.
  - Blocks can be used to perform a variety of actions, from simple data transformations to complex machine learning models.
- `Unique functionality`:
  - Sensors: trigger on some events
    - conditionals: branching logic and if-else logic
    - dynamic: create dynamic children
    - webhooks: additional functionality
  - Data integration
    - unified pipelines: passing objects between data pipelines
    - multi-user environments
    - templating

Mage ***accelerates*** pipeline development

- Hybrid environment
  - Use our GUI for interactive development
  - Use blocks as testable, reusable pieces of code
- Improved DevEx
  - Code and test in parallel
  - Reduce your dependencies, switch tools less, be efficient

Engineering best-practices ***built-in***

- **In-line** testing and debugging
  - Familar, notebook-style format
- Fully-featured observability
  - Transformation in on place: bdt models, streaming, and more
- DRY principles
  - No more DAGs with duplicate functions and weird imports
  - DEaaS

***Reduce time in undifferentiated work***

### Configuring Mage

Follow the instructions [here](https://github.com/mage-ai/mage-zoomcamp).

First, get start by cloning the repo:

```bash
git clone https://github.com/mage-ai/mage-zoomcamp.git mage-zoomcamp
```

Navigate to the repo:

```bash
cd mage-zoomcamp
```

Rename `dev.env` to simply `.env` to ***ensure*** the file is not committed to Git by accident, since it will contain credentials in the future.

```bash
cp dev.env .env
```

- `.env` file contains environment variables for your project. we rename the file because we might put secrets in that file. So we change the filename so that it will be contained in the `gitignore` file and not included in the git repo.

- We can use `ls -la` to see all the files in the directory and find the `.gitignore` file:

  ```bash
  # Environments
  .env
  .venv
  .DS_Store
  env/
  venv/
  ENV/
  env.bak/
  venv.bak/
  ```

Now, let's build the container:

```bash
docker compose build
```

Finally, start the Docker container:

```bash
docker compose up
```

Now, navigate to http://localhost:6789 in your browser. You're ready to get started with the course.

> Note: use `docker pull mageai/mageai:latest` to get the latest image.

### A Simple Pipeline

<img src="./image-02/pipeline-tree.png" alt="pipeline-tree" style="zoom:70%;" />

From the figure we can see that:

- reading from an API
- filling missing values
- exporting it to a local dataframe

Clike *Edit pipeline* in the side bar, we can see a file tree in the left. Let's read the code. We have 3 blocks here:

- Data loader

  ```python
  @data_loader
  def load_data_from_api(**kwargs) -> DataFrame:
      """
      Template for loading data from API
      """
      url = 'https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv?raw=True'
  
      return pd.read_csv(url)
  ```

  Click on the `run` button, we can see the CSV file loaded.

- Transformer. If we click on the run button again, we can see the CSV file after transformation. The two blocks are connected which means data frames that are returned are going to be passed between the 2.

- Data exporter. Uses the output of block 2 as input.

## ETL: API to Postgres

Now, let's build a *real* pipeline. In this section, we'll build a simple ETL pipeline that loads data from an API into a *Postgres* database. Our database will be built using Docker— it will be running locally, but it's the same as if it were running in the cloud.

### Configuring Postgres

In the `docker-compose.yml` file, we have 2 services.

- `magic`: Mage instance
- `postgres`: pulling down the postgres image, and running a local instance. 
  - One thing to mention: we define our `env` variables in the `.env` file. If you already have `postgres` and the port `5432` is already in use, change the `POSTGRES_PORT` to `5433`.

```dockerfile
version: '3'
services:
  magic:
    image: mageai/mageai:latest
    command: mage start ${PROJECT_NAME}
    env_file:
      - .env
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      USER_CODE_PATH: /home/src/${PROJECT_NAME}
      POSTGRES_DBNAME: ${POSTGRES_DBNAME}
      POSTGRES_SCHEMA: ${POSTGRES_SCHEMA}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST: ${POSTGRES_HOST}
      POSTGRES_PORT: ${POSTGRES_PORT}
    ports:
      - 6789:6789
    volumes:
      - .:/home/src/
      - ~/Documents/secrets/personal-gcp.json:/home/src/personal-gcp.json
    restart: on-failure:5
  postgres:
    image: postgres:14
    restart: on-failure
    container_name: ${PROJECT_NAME}-postgres
    env_file:
      - .env
    environment:
      POSTGRES_DB: ${POSTGRES_DBNAME}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    ports:
      - "${POSTGRES_PORT}:5432"
```

- All our environment variables are in the `.env` file.
- We pull variables locally and then inject then into our Docker containers. Since `.env` is in `gitignore`, so we don't have to worry about accidentally committing those files to Version Control and exposing our passwords.

Now we switch to the Mage GUI, go to *files*, now we are in the `io_conifg.taml` file where we manage our connections. 

![config](./image-02/config.png)

We have some default `postgres` connections and connections to other databases. We can make some profile like `Dev` which is useful for our **develop separating development and production**.

Add the below content in the end of the file:

```yaml
dev:
  POSTGRES_CONNECT_TIMEOUT: 10
  POSTGRES_DBNAME: "{{ env_var('POSTGRES_DBNAME') }}"
  POSTGRES_SCHEMA: "{{ env_var('POSTGRES_SCHEMA') }}"
  POSTGRES_USER: "{{ env_var('POSTGRES_USER') }}"
  POSTGRES_PASSWORD: "{{ env_var('POSTGRES_PASSWORD') }}"
  POSTGRES_HOST: "{{ env_var('POSTGRES_HOST') }}"
  POSTGRES_PORT: 5432
```

- We pull in our environment variables here what are beging passed in docker.
- Here we use the syntax like `Jinja` and `dbt(Data Built Tool)` which is done with 2 brackets to interpolate environment variables. It's just a way of interpolating variables that takes injecting variables into strings and we use the `env_var()` syntax.
  - `Jinja`: Jinja is a template engine for Python that allows the use of specific syntax in templates to generate dynamic content. `{{ ... }}` and `{% ... %}` are common syntax markers in Jinja used to **denote variables and control structures**.
  - `dbt`: dbt is an open-source tool used for analyzing and transforming data, and it utilizes Jinja for constructing data models and SQL queries. In dbt, `{{ ... }}` and `{% ... %}` are also used for inserting variables and controlling the construction and execution of data models.

Now we have a `Dev` profile with a bunch of postgres configuration settings that's being pulled in from Docker where we actually define the `postgres` instance.

Navigate over to the `Pipelines`, let's now create a pipeline.

- *Edit* > *Pipeline settings* > *Name*: test_config

- *Data loader* > *SQL* > *Name*: test_postgres > *create*
- *Connection*: PostgreSQL
- *Profile*: dev 
- *Use raw sql*: which removes a lot of templating, what you type is exactly what's being run.

Now run the below query to connect to our database and run it in postgres.

```postgresql
SELECT 1;
```

![data_loader](./image-02/data_loader.png)

Now we can see the returned result. Our postgres connection is established and we have connection to our local postgres instance.

### Writing an ETL Pipeline

In this module we're going to talk about loading data from an API that takes the form of a compressed CSV file.

#### Data loader

- Start a new batch pipeline, and rename it to "api_to_postgres"
- Data loader > Python > API > rename to "load_api_data"

```python
@data_loader
def load_data_from_api(*args, **kwargs):
    """
    Template for loading data from API
    """
    url = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz'

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
    
    parse_dates = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']

    return pd.read_csv(url, sep=',', compression='gzip', dtype=taxi_dtypes, parse_dates=parse_dates)

```

- Go through the dataset and map data types. It can be really powerful in data engineering and specifically with pandas. Letting pandas know what to expect for the column types drastically reduces the memory usage that pandas is going to incur by processing this dataset.[**memory consumption**]
- It's an implicit assertion and if the data type change the pipeline is going to fail and we can get notified.
- Return the csv, here we have serveral parameters:
  - `url`: we use compressed file but pandas are able to deal with it.
  - `sep`: used to specify the delimiter between fields.
  - `compression`: used to specify the compression format of the data file.
  - `dtype`: used to decalre the type of the columns
  - `parse_date`: list parse dates and pandas will parse the columns to an appropriate time stamp automatically.

In Mage, we can do in-line testing. Let's run the code and see the output.

![output_dataloader](./image-02/output_dataloader.png)

#### Transformer

Now we gonna do some transformation. Let's create a generic python transformer names `transform_taxi_data`.

From last step we can see that the `passenger_count` column have `0` values which seems like anomalous data. We want to reomve these data.

```python
@transformer
def transform(data, *args, **kwargs):
    print(f"Preprocessing: rows with zero passengers: {data['passenger_count'].isin([0]).sum()}")
    
    return data[data['passenger_count'] > 0]

@test
def test_output(output, *args):
    assert output['passenger_count'].isin([0]).sum() == 0, "There are rides with 0 passengers"
```

- `data['passenger_count'].isin([0]).sum()`: count the number of rows containing `0` values.

- We return rows with passenger count greater than 0.

- `test_output`: we add an assertion here.

  ```python
  assert condition, message
  ```

  - `condition` is a boolean expression indicating the condition to be validated.
  - `message` is an optional error message, used to provide more specific information is not met.
  - First evaluate the condition, if the condition mets, continues execution. If not met, raise an `AssertionError` exception and output the error message.

![test_output](./image-02/test_output.png)

Now we can see the output and the test passed.

#### Data exporter

Let's add an python data exporter named "taxi_data_to_postrges" to export our data to postgres.

```python
@data_exporter
def export_data_to_postgres(df: DataFrame, **kwargs) -> None:
    """
    Template for exporting data to a PostgreSQL database.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#postgresql
    """
    schema_name = 'ny_taxi'  # Specify the name of the schema to export data to
    table_name = 'yellow_cab_data'  # Specify the name of the table to export data to
    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'dev'

    with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
        loader.export(
            df,
            schema_name,
            table_name,
            index=False,  # Specifies whether to include index in exported table
            if_exists='replace',  # Specify resolution policy if table name already exists
        )
```

- `schema`: we have to define the schema.
- `config_profile`: we use `dev` as before.
- `if_exists`: if the table exists, then replace it.

![data_exporter](./image-02/data_exporter.png)

Now we can see we have successfully export the data to the database. We can use a SQL data loader to check this. Select the `connection` and other settings as before.

```postgresql
SELECT * FROM ny_taxi.yellow_cab_data LIMIT 10;
```

We can see the output which means we have successfully build the pipeline:

![data-loader](./image-02/data-loader.png)



## ETL: API to GCS

### Configuring GCP

In this module we will use GCP for mage to read and write data.

- Create a `google storage bucket`:  go to GCP and search 'google cloud storage', create a new ` bucket `named 'mage-zoomcamp-lbw-3'. Leave the rest of the Settings unchanged and click `create`. What we created is a cloud storage file system for us to interact with and engage with.

- Mage uses `service account` to connect to GCP. It's like a set of permissions that you are granting and credentials associated with those permissions. 

  - Create a new `service account` named 'mage-zoomcamp'.
  - Role: *Basic* > *Owner*, allowing us to edit everything in GCS and BIgQuery
  - After created, go to *Keys* > *Add Key* > *Create new key* > *JSON*
  - Copy the JSON file to the Mage directory

- In the `Dockerfile`, we defined `volume` for Mage:

  ```dockerfile
  - .:/home/src/
  ```

  All the files in the directory are going to be pulled into Mage and live in that Mage container including the credential file (JSON).

- Now go to Mage page and go to the `io_config.yaml` file.

  ```yaml
  GOOGLE_SERVICE_ACC_KEY:
      type: service_account
      project_id: project-id
      private_key_id: key-id
      private_key: "-----BEGIN PRIVATE KEY-----\nyour_private_key\n-----END_PRIVATE_KEY"
      client_email: your_service_account_email
      auth_uri: "https://accounts.google.com/o/oauth2/auth"
      token_uri: "https://accounts.google.com/o/oauth2/token"
      auth_provider_x509_cert_url: "https://www.googleapis.com/oauth2/v1/certs"
      client_x509_cert_url: "https://www.googleapis.com/robot/v1/metadata/x509/your_service_account_email"
    GOOGLE_SERVICE_ACC_KEY_FILEPATH: "/path/to/your/service/account/key.json"
    GOOGLE_LOCATION: US # Optional
  ```

  We can see there are 2 ways to authenticate with Google:

  - Past JSON payload: replace the content from `type` to `client` with the data in our credential JSON file.

  - Just use the `GOOGLE_SERVICE_ACC_KEY_FILEPATH`. We gonna use this method and delete the payload rows.

    ```yaml
    GOOGLE_SERVICE_ACC_KEY_FILEPATH: "/path/to/your/service/account/key.json"
    GOOGLE_LOCATION: US # Optional
    ```

    Our volume is mounted, now go to the `terminal` of Mage, we can see we're already in the `/home/src` directory. And we have our credentials JSON file here. Now we can set the path:

    ```yaml
    GOOGLE_SERVICE_ACC_KEY_FILEPATH: "/home/src/dtc-de-412517-6c19c84f6d2e.json"
    GOOGLE_LOCATION: US # Optional
    ```

Now Mage knows where is our credential file and when we use any block with GCP, Mage is going to use that service account in order to execute the cell.

- Set the connection to `BigQuery`.

- Set the profile to `default`.

  ![bigquery](./image-02/bigquery.png)

Now we are able to use BigQuery. Let's go to the `example_pipeline` which load a Titanic dataset and then write it to a file. Run the pipeline, we will load that csv file, process it and write it to a local file in our Mage Project. Now we get a `titanic_clean.csv` file. Then we want to upload this file to GCS.

Go to the GCS and go to our bucket (mage-zoomcamp-lbw-3). Upload our csv file there.

![GCS_csv](./image-02//GCS_csv.png)

Go back to our `test_config` pipeline. Now we gonna test if the GCS works.

- *Data loader* > *Python* > *Google Cloud Storage* > *Name*: test_gcs
- `bucket_name`: mage-zoomcamp-lbw-3
- `object_key`: titanic_clean.csv

![test_GCS](./image-02/test_GCS.png)

We are able to connect to GCS. What we had to do is create a service account, drop that json in our local development environment and now we can connect to BigQuery and GCS. The next steps we gonna build pipelines that use GCS and BigQuery.

### Writing an ETL Pipeline

#### Single parquet file

Start a new batch pipeline. We have already write the code before so just drag the `load_api_data.py` block over. We can also reuse our transformer so drag the `transform_taxi_data.py`.

![log_api_reuse](./image-02/log_api_reuse.png)

Now attach these blocks.

![tree_of_block](./image-02/tree_of_block.png)

Add a `Data exporter` to GCS named 'taxi_to_gcs_parquet': 

- `bucket_name`: mage-zoomcamp-lbw-3
- `object_key`: nyc_taxi_data.parquet

![data_exporter_gcs](./image-02/data_expoter_gcs.png)

Execute the upstream blocks.

```
GoogleCloudStorage initialized


└─ Exporting data frame to bucket 'mage-zoomcamp-lbw-3' at key 'nyc_taxi_data.parquet'...

DONE
```

![upload_parquet](./image-02/upload_parquet.png)

Now we can see that the parquet file has been uploaded to GCS.

#### Partitioned parquet files

In data engineering, we don't write a large dataset into a single parquet file. So let's write it into a partitioned parquet file where we break a dataset up by some rows or characteristic. Partitioned by ***date*** is often useful.

Create a *Data Exporter* > *Python* > *Generic (no template)* > *Name*: taxi_to_gcs_partitioned_parquet. Connect it to the Transformer.

Here we define our credentials manually and use `PyArrow` library to partition the dataset.

- Tell `PyArrow` where our credential is. Before we set this in the config file, but now we do it manually:

  ```python
  os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/src/dtc-de-412517-6c19c84f6d2e.json"
  ```

- Define the bucket name, project id, table name and root path.

  ```python
  bucket_name = 'mage-zoomcamp-lbw-3'
  project_id = 'dtc-de-412517'
  table_name = "nyc_taxi_data"
  root_path = f'{bucket_name}/{table_name}'
  ```

- `PyArrow` is a Python implementation of Apache Arrow, providing efficient and fast methods for handling columnar data in Python.

- Now we gonna partition the data by `date`. First create a date time column.

  ```python
  data['tpep_pickup_date'] = data['tpep_pickup_datetime'].dt.date
  ```

  `.dt` is a property in pandas used to access date-time related methods and attributes. `.dt.date` is used to extract the date portion and convert it into a date object.

- For `PyArrow` we need to define a pyarrow table. Convert the pandas DataFrame object `data` to an Apache Arrow Table object `table`.

  ```python
  table = pa.Table.from_pandas(data)
  ```

-  Through this object, you can interact with files on Google Cloud Storage, such as reading, writing, deleting, and other operations. This file system object is going to authorize using our environment variable automatically.

  ```python
  gcs = pa.fs.GcsFileSystem()
  ```

- Now we use the `write_to_dataset` function.

  ```python
  pq.write_to_dataset(
        table,
        root_path=root_path,
        partition_cols=['tpep_pickup_date'],
        filesystem=gcs
    )
  ```

  - `table`: our pyarrow table.
  - `root_path`: our root path.
  - `partition_cols`: columns to partition on, has to be a list.
  - `filesystem`: our GCS file system.

Now the whole data exporter looks like:

```python
import pyarrow as pa # we have included this in Docker, so it would be installed by default
import pyarrow.parquet as pq
import os # necessary for getting environment variables

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter

# set an environment variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/src/dtc-de-412517-6c19c84f6d2e.json"

bucket_name = 'mage-zoomcamp-lbw-3'
project_id = 'dtc-de-412517'

table_name = "nyc_taxi_data"

root_path = f'{bucket_name}/{table_name}'


@data_exporter
def export_data(data, *args, **kwargs):
    data['tpep_pickup_date'] = data['tpep_pickup_datetime'].dt.date

    table = pa.Table.from_pandas(data)

    gcs = pa.fs.GcsFileSystem()

    pq.write_to_dataset(
        table,
        root_path=root_path,
        partition_cols=['tpep_pickup_date'],
        filesystem=gcs
    )
```

If we partition a large dataset there are a lot of advantages to ***quering the data*** but also ***reading and writing IO operations***. Now we can see our parquet files partitioned by date. If we want to query data of a certain date, we can only read from the corresponding parquet folder instead of reading the whole dataset. It would be more efficient.

![partitioned_parquet](./image-02/Partitioned_parquet.png)



## ETL: GCS to BigQuery

### ETL Pipeline

Now that we've written data to GCS, let's load it into BigQuery. In this section, we'll walk through the process of using Mage to load our data from GCS to BigQuery. This closely mirrors a very common data engineering workflow: loading data from a ***data lake*** into a ***data warehouse***.

- Create a new pipeline named 'gcs_to_bigquery'.

- Create a python GCS Data Loader named 'load_taxi_gcs'. Here we use the unpartitioned data.

  ```python
  bucket_name = 'mage-zoomcamp-lbw-3'
  object_key = 'nyc_taxi_data.parquet'
  ```

- Now we got our dataset, we gonna do some transformation. Create a generic pythonTransformer named 'transform_staged_data'. We will standardize the column names.

  ```python
  @transformer
  def transform(data, *args, **kwargs):
      data.columns = (data.columns
                      .str.replace(' ', '_')
                      .str.lower()
      )
  
      return data
  ```

  - Replace any spaces with underscores.
  - Lower any capital letters.

- Now we have standardized our columns, let's export our data. Create a SQL data exporter named 'write_taxi_to_bigquery'.

  - Use `BigQuery` and `default` connection.

  - Set the schema to `ny_taxi` and table name to `yellow_cab_data`.

  - We use to insert all rows from transform_staged_data into a table.

    ```python
    SELECT * FROM {{ df_1 }};
    ```

Now go to Google BigQuery we can see our dataset.

![bigquery-dataset](./image-02/bigquery-dataset.png)

### Trigger

We have our pipeline working and Mage is an orchestrator so we need to schedule our workflows. A ***trigger*** is a set of instructions that determine when or how a pipeline should run. We build pipelines, schedule them, and chain the pipelines together.

Go to `triggers` which schedule workflows in Mage.

![scheduler](./image-02/scheduler.png)

![trigger](./image-02/trigger.png)

Enable the trigger and then we can see the status of our pipeline. Trigger can also be event-based. If some events happened then the workflow will be triggered.



## Parameterized Execution

### Parameterized Execution

By now you're familiar with building pipelines, but what about adding parameters? In this video, we'll discuss some ***built-in runtime variables*** that exist in Mage and show you how to define your own! We'll also cover how to use these variables to ***parameterize your pipelines***. Finally, we'll talk about what it means to **backfill** a pipeline and how to do it in Mage.

We didn't load a partial dataset before. We have DAG and our pipeline and the execution of that pipeline is dependent on some variables. In Mage there are different types of variables like runtime variables, Global variables.

Today we gonna talk about runtime variables which would be useful when you call an API and want to write data to a specific parquet file by date. Let's go to the `load_nyc_taxi_data` pipeline and ***clone*** it.

> Note: blocks in Mage are shared, if you edit blocks you will be editing blocks across every pipeline that they exist in.

- Delete the 'taxi_to_gcs_partitioned_parquet' block. 
- Add a new generic Data Exporter named 'export_taxi_to_gcp_parameter'.
- Copy the code from 'taxi_to_gcs_parquet' block and delete the 'taxi_to_gcs_parquet' block .
- Rename the pipeline with 'load_to_gcp_parameterized'.

![parameterized_pipeline](./image-02/parameterized_pipeline.png)

Now the pipeline should look like this. We can notice that every Mage block has `**kwargs` (keyword arguments) which contains a number of parameters. Any variable you declare and pass into pipeline is going to be stored in the keyword arguments. We can access some by default like `execution date`.

```python
now = kwargs.get('execution_date')
print(now)
# return the date
print(now.date())
# return the customized date
print(now.strftime("%Y/%m/%d"))
```

Run this and we will get the below output:

```
2024-02-03 18:18:35.923002

2024-02-03

2024/02/03
```

If we are going to write incremental data, we can define the path.

```python
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.google_cloud_storage import GoogleCloudStorage
from pandas import DataFrame
from os import path

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_google_cloud_storage(df: DataFrame, **kwargs) -> None:
    """
    Template for exporting data to a Google Cloud Storage bucket.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#googlecloudstorage
    """

    now = kwargs.get('execution_date')
    # define the path
    now_fpath = now.strftime("%Y/%m/%d")

    print(now)


    config_path = path.join(get_repo_path(), 'io_config.yaml')
    config_profile = 'default'

    bucket_name = 'mage-zoomcamp-lbw-3'
    object_key = f'{now_fpath}/daily-trips.parquet'

    GoogleCloudStorage.with_config(ConfigFileLoader(config_path, config_profile)).export(
        df,
        bucket_name,
        object_key,
    )

```

```
2024-02-03 19:22:56.846016

GoogleCloudStorage initialized

 

└─ Exporting data frame to bucket 'mage-zoomcamp-lbw-3' at key '2024/02/03/daily-trips.parquet'...

DONE
```

Now we can see the data has been uploaded to the bucket.



### Backfills

Now we gonna talking about ***backfilling pipelines***. We just discussed parameterized execution which run pipelines with some dependency on a variable like the date. Imagine you have lost some data or missed some data and you need to rerun the pipelines for multiple days, weeks, months. Here we will see how we can create ***backfill functionality*** to replicate lost data or data for parameterized runs that you need to backfill.

Go to the parameterized pipeline we just made. Click the `Backfill` module, and create a new backfill.

![backfill1](./image-02/backfill1.png)

It's going to create serveral runs and it's going to assign the execution variables that we referenced in last module to each day in this pipeline. For each run the execution date is different and it's very useful for parameterized pipelines that use execution variables.

![backfill_pipelines](./image-02/backfill_pipelines.png)
