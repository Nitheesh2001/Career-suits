import json
import hashlib

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to authenticate user
def authenticate_user(username, password, users):
    if username in users and users[username] == hash_password(password):
        return True
    return False

# Function to register a new user
def register_user(username, password, users):
    if username in users:
        return False
    users[username] = hash_password(password)
    with open('users.json', 'w') as f:
        json.dump(users, f)
    return True
