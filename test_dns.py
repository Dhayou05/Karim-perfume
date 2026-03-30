import dns.resolver
from pymongo import MongoClient

# Configure custom DNS nameservers
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']

print("DNS configured to use Google DNS.")

# Test pymongo SRV
uri = "mongodb+srv://karimperfum_db_user:karim-perfm05@cluster0.0n7io2u.mongodb.net/?appName=Cluster0"
try:
    print("Connecting...")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print("Error:", e)
