import pandas as pd
import matplotlib.pyplot as plt

# Read the data from output.csv
data = pd.read_csv('../output.csv')

# Extract the headers for visualization
headers = ['TEXT', 'LABEL']

# Create a bar plot to visualize the data
plt.figure(figsize=(10, 6))
data[headers].groupby('LABEL').count()['TEXT'].plot(kind='bar')
plt.title('Distribution of Labels in the Text Data')
plt.xlabel('Label')
plt.ylabel('Count')
plt.show()