import json

import pandas as pd
import snowflake.connector
import torch
import wandb
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

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

# Tokenize and encode the text data
tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
inputs = tokenizer(df['TEXT'].tolist(), padding=True, truncation=True, max_length=512, return_tensors="pt")


# Create a custom dataset for PyTorch
class CustomDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)


# Split the data into training and validation sets
X_train, X_val, y_train, y_val = train_test_split(inputs, df['LABEL'], test_size=0.2, random_state=42)

# Create custom datasets for training and validation
train_dataset = CustomDataset({key: val[X_train.indices] for key, val in inputs.items()}, y_train.values)
val_dataset = CustomDataset({key: val[X_val.indices] for key, val in inputs.items()}, y_val.values)

# Define training parameters
batch_size = 8
epochs = 3
learning_rate = 5e-5

# Initialize wandb
wandb.init(project="your_project_name",
           config={"epochs": epochs, "batch_size": batch_size, "learning_rate": learning_rate})
config = wandb.config

# Initialize the model
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased')

# Define the optimizer and loss function
optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
loss_fn = torch.nn.CrossEntropyLoss()

# Create a DataLoader for training and validation sets
train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=config.batch_size, shuffle=False)

# Training loop
for epoch in range(config.epochs):
    model.train()
    for batch in train_loader:
        optimizer.zero_grad()
        input_ids = batch['input_ids']
        attention_mask = batch['attention_mask']
        labels = batch['labels']
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
        loss = outputs.loss
        loss.backward()
        optimizer.step()
        wandb.log({"train_loss": loss.item()})

    # Validation loop
    model.eval()
    val_loss = 0
    correct_preds = 0
    total_preds = 0
    with torch.no_grad():
        for batch in val_loader:
            input_ids = batch['input_ids']
            attention_mask = batch['attention_mask']
            labels = batch['labels']
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss
            val_loss += loss.item()
            logits = outputs.logits
            preds = torch.argmax(logits, dim=1)
            correct_preds += torch.sum(preds == labels).item()
            total_preds += len(labels)
    val_loss /= len(val_loader)
    val_accuracy = correct_preds / total_preds
    wandb.log({"val_loss": val_loss, "val_accuracy": val_accuracy})

wandb.finish()
