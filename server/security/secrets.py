import os

# Load from environment variables if available, else fall back to hardcoded defaults
SECRET_KEY = os.getenv("HYPERINDEX_SECRET_KEY", "super-secret-key-change-me")
ALGORITHM = "HS256"