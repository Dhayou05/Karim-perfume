import json
import os
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
from dotenv import load_dotenv
import certifi

# Load environment variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATA_FILE = 'perfumes.json'

def migrate_data():
    if not os.path.exists(DATA_FILE):
        print(f"Error: {DATA_FILE} not found. Nothing to migrate.")
        return

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        perfumes = json.load(f)

    if not perfumes:
        print("No data found in JSON to migrate.")
        return

    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.perfume_store
    perfumes_collection = db.perfumes

    print(f"Loaded {len(perfumes)} perfumes from JSON. Inserting into MongoDB...")

    # Clear existing data to avoid duplicates (optional, based on requirement)
    perfumes_collection.delete_many({})

    try:
        result = perfumes_collection.insert_many(perfumes)
        print(f"Successfully migrated {len(result.inserted_ids)} perfumes to MongoDB.")
    except BulkWriteError as bwe:
        print("Error during insertion:", bwe.details)
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == '__main__':
    migrate_data()

