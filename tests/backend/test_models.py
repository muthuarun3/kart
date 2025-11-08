import pytest
from sqlmodel import SQLModel, create_engine, Session
from datetime import date
from typing import Optional

from src.backend.models import Circuit, Course

# --- Configuration de la base de données SQLite en mémoire ---
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

# --- Test 1 : Création d'un Circuit ---
def test_creer_circuit(db_session):
    circuit = Circuit(
        Nom_Circuit="Circuit de Monaco",
        Configuration_Piste="Grand Prix",
        Longueur="3.337 km",
        Adresse="Monte Carlo, Monaco"
    )
    db_session.add(circuit)
    db_session.commit()
    db_session.refresh(circuit)
    assert circuit.id is not None
    assert circuit.Nom_Circuit == "Circuit de Monaco"

# --- Test 2 : Création d'une Course ---
def test_creer_course(db_session):
    circuit = Circuit(
        Nom_Circuit="Circuit de Monaco",
        Configuration_Piste="Grand Prix",
        Longueur="3.337 km",
        Adresse="Monte Carlo, Monaco"
    )
    db_session.add(circuit)
    db_session.commit()

    course = Course(
        Section=1,
        Pilote="Lewis Hamilton",
        Date=date(2025, 11, 4),
        Kart=42,
        Note=10,
        Meilleur_Tour="1:30.000",
        Ecart="0.500",
        Tours=20,
        Humidite=45.5,
        circuit_id=circuit.id
    )
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)
    assert course.id is not None
    assert course.Pilote == "Lewis Hamilton"

# --- Test 3 : Relation entre Circuit et Course ---
def test_relation_circuit_course(db_session):
    circuit = Circuit(
        Nom_Circuit="Circuit de Monaco",
        Configuration_Piste="Grand Prix",
        Longueur="3.337 km",
        Adresse="Monte Carlo, Monaco"
    )
    db_session.add(circuit)
    db_session.commit()

    course = Course(
        Section=1,
        Pilote="Lewis Hamilton",
        Date=date(2025, 11, 4),
        Kart=42,
        Note=10,
        Meilleur_Tour="1:30.000",
        Ecart="0.500",
        Tours=20,
        Humidite=45.5,
        circuit_id=circuit.id
    )
    db_session.add(course)
    db_session.commit()

    # Vérifie que la course est bien liée au circuit
    db_session.refresh(circuit)
    assert len(circuit.courses) == 1
    assert circuit.courses[0].Pilote == "Lewis Hamilton"

# --- Test 4 : Contrainte d'unicité sur Circuit ---
def test_contrainte_unicite_circuit(db_session):
    circuit1 = Circuit(
        Nom_Circuit="Circuit de Monaco",
        Configuration_Piste="Grand Prix",
        Longueur="3.337 km",
        Adresse="Monte Carlo, Monaco"
    )
    db_session.add(circuit1)
    db_session.commit()

    # Tentative d'ajout d'un circuit avec le même (Nom_Circuit, Configuration_Piste)
    circuit2 = Circuit(
        Nom_Circuit="Circuit de Monaco",
        Configuration_Piste="Grand Prix",
        Longueur="3.337 km",
        Adresse="Monte Carlo, Monaco"
    )
    db_session.add(circuit2)

    # Doit lever une exception à cause de la contrainte d'unicité
    with pytest.raises(Exception):
        db_session.commit()
