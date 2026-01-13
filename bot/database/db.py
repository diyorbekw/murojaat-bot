"""
Database instance initialization
"""

from bot.config import config
from bot.database.models import Database

# Create global database instance
db = Database(config.DATABASE_PATH)