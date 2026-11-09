import os
import pymongo
from dotenv import load_dotenv

load_dotenv()

MONGO_DB_URL = os.getenv("MONGO_DB_URL")

client = pymongo.MongoClient(MONGO_DB_URL)

database = client["NetworkSecurity"]

collection = database["NetworkData"]

# Delete all inserted records
result = collection.delete_many({})

print("Total deleted records:", result.deleted_count)

client.close()