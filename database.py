import os
from pymongo import MongoClient, ASCENDING,DESCENDING
uri=os.getenv("MONGODB_URI")

if not uri:
    raise RuntimeError("MONGODB_URI environment variable not found")

client=MongoClient(uri,serverSelectionTimeoutMS=5000)
db=client["ip_logger"]

visitors=db["visitors"]
request_windows=db["request_windows"]
blocked_ips=db["blocked_ips"]   

def setup_indexes():
    visitors.create_index([("ip", ASCENDING), ("timestamp", DESCENDING)])
    request_windows.create_index([("ip", ASCENDING), ("window_start", ASCENDING)], unique=True)
    request_windows.create_index([("expire_at", ASCENDING)], expireAfterSeconds=0)
    blocked_ips.create_index([("ip", ASCENDING)], unique=True)

if __name__ == "__main__":
    client.admin.command("ping")
    setup_indexes()
    print("Database connected. Indexes created successfully.")
    client.close()

