from pymongo import MongoClient
uri = "mongodb+srv://venkatasivaprasad9493_db_user:ri7NHxHk7NzoWE3Q@cluster0.z5mxiwm.mongodb.net"
client = MongoClient(uri)
try:
    client.admin.command("ping")
    print("Connected successfully")
    client.close()

except Exception as e:
    raise Exception(
        "The following error occurred: ", e)