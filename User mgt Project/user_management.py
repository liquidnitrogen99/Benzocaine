# Mongo Datbase = "user_management"
# Collection Name = "users"

# Document Format in Mongo Collection...
# {
#   "_id": ObjectId("5f50c31e1c4ae837d656f705"),
#   "username": "test_user",
#   "email": "test@example.com"
# }


from pymongo import MongoClient

# MongoDB client connection
client = MongoClient('localhost', 27017)
db = client.user_management_db

def add_user(username, email):
    if db.users.find_one({"username": username}):
        return "User already exists"

    db.users.insert_one({"username": username, "email": email})
    return "User added"

def get_user(username):
    user = db.users.find_one({"username": username}, {"_id": 0})
    if user:
        return user
    return "User not found"

def delete_user(username):
    result = db.users.delete_one({"username": username})
    if result.deleted_count > 0:
        return "User deleted"
    return "User not found"

