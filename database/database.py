import os
from pathlib import Path

from pymongo import MongoClient
from dotenv import load_dotenv


# Project root folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env
env_file = BASE_DIR / ".env"
load_dotenv(env_file)

# Get MongoDB connection string
MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise ValueError(
        f"MONGODB_URI not found in .env file.\n"
        f"Expected .env location: {env_file}"
    )

# Connect to MongoDB
client = MongoClient(MONGODB_URI)

# Select database
db = client["ai_teacher_db"]


# Collections
students_collection = db["students"]
documents_collection = db["documents"]
lessons_collection = db["lessons"]
learning_sessions_collection = db["learning_sessions"]
quiz_questions_collection = db["quiz_questions"]
quiz_attempts_collection = db["quiz_attempts"]
assessments_collection = db["assessments"]
progress_collection = db["progress"]
weekly_tests_collection = db["weekly_tests"]
recommendations_collection = db["recommendations"]


# Test connection
def test_connection():

    try:
        client.admin.command("ping")

        print("----------------------------------")
        print("MongoDB connected successfully!")
        print("Database:", db.name)
        print("----------------------------------")

    except Exception as e:

        print("----------------------------------")
        print("MongoDB connection failed!")
        print("Error:", e)
        print("----------------------------------")


if __name__ == "__main__":
    test_connection()