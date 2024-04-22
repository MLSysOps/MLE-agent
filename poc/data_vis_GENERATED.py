import pandas as pd
import matplotlib.pyplot as plt

# Read the data from output.csv
data = pd.read_csv('output.csv')

# Define the header of the data you want to visualize
header = 'text, label'

# Split the header into individual column names
columns = [col.strip() for col in header.split(',')]

# Create the plot
plt.figure(figsize=(10, 6))
plt.bar(data[columns[0]], data[columns[1]])
plt.xlabel(columns[0])
plt.ylabel(columns[1])
plt.title('Visualization of ' + columns[0] + ' vs ' + columns[1])
plt.show()