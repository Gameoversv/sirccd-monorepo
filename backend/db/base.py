"""
Base declarativa de SQLAlchemy
"""

from sqlalchemy.ext.declarative import declarative_base

# Base para todos los modelos
Base = declarative_base()

# Metadata para migraciones
metadata = Base.metadata
