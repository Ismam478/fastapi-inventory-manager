from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import urllib.parse


# 1. Encode the password to handle the '@' symbol
password = urllib.parse.quote_plus("**********")


# 2. Construct the URL using the encoded password
db_url = f"postgresql://postgres:{password}@localhost:5432/Nexora"


# 3. Create the engine
engine1 = create_engine(db_url)

Session1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)

# ========== PostgreSQL Configuration (Uncomment to use) ==========
# import urllib.parse
# password = urllib.parse.quote_plus("Negom@ggs69")
# db_url = f"postgresql://postgres:{password}@localhost:5432/Nexora"
# engine1 = create_engine(db_url)
# Session1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)