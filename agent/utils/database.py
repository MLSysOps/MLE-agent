import lancedb
import pandas as pd
import pyarrow as pa

if __name__ == '__main__':
    db = lancedb.connect("data/sample-lancedb")
    data = [
        {"vector": [3.1, 4.1], "item": "foo", "price": 10.0},
        {"vector": [5.9, 26.5], "item": "bar", "price": 20.0},
    ]

    # Synchronous client
    tbl = db.create_table("my_table", data=data)
