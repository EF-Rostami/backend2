import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ✅ Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ✅ Import your Base and models
from database import Base  # Base = declarative_base() in database.py
import models  # Ensures all models are imported

# Interpret the config file for Python logging.
config = context.config
fileConfig(config.config_file_name)

# Set your metadata object
target_metadata = Base.metadata
