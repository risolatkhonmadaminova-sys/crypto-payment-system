from app.db.database import engine, Base
from app.db import models


# Create all database tables
Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")