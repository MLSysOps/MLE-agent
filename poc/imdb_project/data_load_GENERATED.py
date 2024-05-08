import json

import pandas as pd
import snowflake.connector

# Load snowflake credentials from file
with open('../snowflake_key.json', 'r') as f:
    snowflake_credentials = json.load(f)

# Connect to snowflake
conn = snowflake.connector.connect(
    user=snowflake_credentials['user'],
    password=snowflake_credentials['password'],
    account=snowflake_credentials['account'],
    warehouse=snowflake_credentials['warehouse'],
    database=snowflake_credentials['database'],
    schema=snowflake_credentials['schema']
)

# Generate SQL query
query = "SELECT * FROM IMDB_TRAIN"

# Execute the SQL query and load data into a DataFrame
df = pd.read_sql(query, conn)

# Close the connection
conn.close()

# Show some data from the DataFrame
print(df.head())
