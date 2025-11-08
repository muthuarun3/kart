from datetime import date
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship


# --- CLASSE DE BASE POUR LE CIRCUIT (Sera une table SQL) ---
class Circuit(SQLModel, table=True):
    # Clé primaire du circuit
    id: Optional[int] = Field(default=None, primary_key=True)

    # Les champs du circuit (Nom_Circuit et Configuration_Piste forment la clé logique)
    Nom_Circuit: str = Field(index=True)
    Configuration_Piste: str = Field(index=True)
    Longueur: str
    Adresse: str

    # Relation : un circuit peut avoir plusieurs courses
    courses: list["Course"] = Relationship(back_populates="circuit")

    # Clé unique pour éviter les doublons de circuit/piste
    __table_args__ = (
        {"unique_constraint": "uq_circuit_piste"}
    )


# --- CLASSE DE BASE POUR LA COURSE (Sera une autre table SQL) ---
class Course(SQLModel, table=True):
    # Clé primaire de la course
    id: Optional[int] = Field(default=None, primary_key=True)

    Section: int
    Pilote: str
    Date: date
    Kart: Optional[int]
    Note: int
    Meilleur_Tour: str
    Humidite: float  # Utilisation de float pour la simplicité de l'ORM

    # Clé étrangère vers la table Circuit
    circuit_id: int = Field(foreign_key="circuit.id")

    # Relation : une course appartient à un circuit
    circuit: Circuit = Relationship(back_populates="courses")
