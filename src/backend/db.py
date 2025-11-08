from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session


# Nom du fichier de base de données SQLite
sqlite_file_name = "karting_data.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)


def create_db_and_tables():
    """Crée les tables dans la base de données."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dépendance FastAPI pour obtenir une session de DB."""
    with Session(engine) as session:
        yield session
