from pymongo import MongoClient

uri = "mongodb+srv://adri-ayala:Pickles254@gridfit.szhbvt2.mongodb.net/?retryWrites=true&w=majority&appName=GridFit"

try:
    client = MongoClient(uri)
    db = client["GridFit"]
    print("Connected to MongoDB!")
    print("Collections:", db.list_collection_names())
except Exception as e:
    print("Connection failed:", e)