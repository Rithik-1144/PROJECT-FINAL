from pymongo import MongoClient
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Connection Setup
def connect_to_mongodb():
    """
    Connects to the MongoDB database and returns the collections for analysis history and users.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/")
        db = client["stress_management"]
        collection = db["analysis_history"]
        user_collection = db["users"]
        logging.info("Connected to MongoDB successfully.")
        return collection, user_collection
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {str(e)}")
        raise Exception(f"Failed to connect to MongoDB: {str(e)}")

# Hash Password for Secure Login
def hash_password(password):
    """
    Hashes the password using SHA-256 for secure storage.
    """
    return hashlib.sha256(password.encode()).hexdigest()

# Save User Data to MongoDB
def save_user_data(username, emotion, daily_routine, stress_level, recommendation):
    """
    Saves user data (emotion, daily routine, stress level, and recommendation) to the database.
    """
    try:
        collection, _ = connect_to_mongodb()
        user_data = {
            "username": username,
            "emotion": emotion,
            "daily_routine": daily_routine,
            "stress_level": stress_level,
            "recommendation": recommendation
        }
        collection.insert_one(user_data)
        logging.info(f"User data saved for {username}.")
    except Exception as e:
        logging.error(f"Failed to save user data: {str(e)}")
        raise Exception(f"Failed to save user data: {str(e)}")

# Register a New User
def register_user(username, password):
    """
    Registers a new user by saving their username and hashed password to the database.
    """
    try:
        _, user_collection = connect_to_mongodb()
        hashed_password = hash_password(password)
        user = {
            "username": username,
            "password": hashed_password
        }
        user_collection.insert_one(user)
        logging.info(f"User {username} registered successfully.")
    except Exception as e:
        logging.error(f"Failed to register user: {str(e)}")
        raise Exception(f"Failed to register user: {str(e)}")

# Authenticate User
def authenticate_user(username, password):
    """
    Authenticates a user by checking their username and password.
    """
    try:
        _, user_collection = connect_to_mongodb()
        hashed_password = hash_password(password)
        user = user_collection.find_one({"username": username, "password": hashed_password})
        if user:
            logging.info(f"User {username} authenticated successfully.")
            return True
        else:
            logging.warning(f"Authentication failed for user {username}.")
            return False
    except Exception as e:
        logging.error(f"Failed to authenticate user: {str(e)}")
        raise Exception(f"Failed to authenticate user: {str(e)}")