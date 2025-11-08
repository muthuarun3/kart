from contextlib import asynccontextmanager  # Nouvel import !
from io import StringIO
from typing import Annotated, AsyncGenerator

import pandas as pd
import numpy as np
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, status
from pydantic import ValidationError
from sqlmodel import Session, select

from backend.utils import export_data_to_csv_response
from backend.db import create_db_and_tables, get_session
from backend.models import Circuit, Course


# --- Définition du Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gère le cycle de vie (démarrage/arrêt) de l'application.
    Remplace @app.on_event("startup").
    """
    print("Démarrage de l'application : Création des tables DB...")
    create_db_and_tables()
    yield
    print("Arrêt de l'application.")
    # Le code après 'yield' s'exécute à l'arrêt (shutdown), si nécessaire.


# Initialisation de l'API avec le lifespan
app = FastAPI(lifespan=lifespan)

# Dépendances
SessionDep = Annotated[Session, Depends(get_session)]


@app.get("/circuits", response_model=list[Circuit], summary="Récupérer tous les circuits")
def read_circuits(session: SessionDep, offset: int = 0, limit: int = 100):
    """
    Récupère une liste de circuits avec pagination.
    """
    # Utilisation de Pydantic/SQLModel pour la validation et la réponse automatique
    circuits = session.exec(select(Circuit).offset(offset).limit(limit)).all()
    return circuits


@app.get("/circuits/{circuit_id}", response_model=Course, summary="Récupérer une course par ID")
def read_circuit_by_id(circuit_id: int, session: SessionDep):
    """
    Récupère une course spécifique par son identifiant unique.
    """
    circuit = session.get(Circuit, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Course non trouvée")
    return circuit


@app.get("/circuits/export", summary="Exporter tous les circuits au format CSV")
async def export_circuits(session: SessionDep):
    """
    Récupère toutes les données de la table 'Circuit' et les retourne au format CSV.
    """
    try:
        # 1. Récupérer les données
        circuits_records = session.exec(select(Circuit)).all()

        # 2. Convertir en DataFrame
        # La méthode model_dump() de SQLModel/Pydantic est utilisée pour obtenir un dictionnaire propre
        data = [c.model_dump() for c in circuits_records]
        df = pd.DataFrame(data)

        if df.empty:
            raise HTTPException(status_code=404, detail="Aucun circuit trouvé pour l'exportation.")

        # 3. Supprimer la colonne 'id' interne (si vous ne voulez pas l'exporter)
        df = df.drop(columns=['id'])

        # 4. Renvoyer le CSV
        return export_data_to_csv_response(df, "export_circuits")

    except HTTPException:
        raise  # Reroute l'exception 404
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'exportation des circuits : {e}")


@app.put("/circuits/import", status_code=status.HTTP_200_OK,
         summary="Mettre à jour/Insérer des circuits via CSV (UPSERT)")
async def upsert_circuits_csv(
        file: UploadFile = File(...),
        session: SessionDep = None
):
    """
    Importe et met à jour les données des circuits à partir d'un fichier CSV.
    La mise à jour est basée sur la clé logique (Nom_Circuit, Configuration_Piste).

    CSV attendu: Circuit, Piste, Longueur, Adresse
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .csv sont acceptés.")

    contents = await file.read()
    buffer = StringIO(contents.decode('utf-8'))

    try:
        df = pd.read_csv(buffer)
        df.columns = [col.strip() for col in df.columns]
        df = df.rename(columns={'Circuit': 'Nom_Circuit', 'Piste': 'Configuration_Piste'})
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Erreur de lecture ou de format CSV: {e}")

    updated_count = 0
    created_count = 0

    for index, row in df.iterrows():
        try:
            # Clé logique pour l'UPSERT
            nom = row['Nom_Circuit']
            piste = row['Configuration_Piste']

            # Rechercher le circuit existant
            statement = select(Circuit).where(
                Circuit.Nom_Circuit == nom,
                Circuit.Configuration_Piste == piste
            )
            existing_circuit = session.exec(statement).first()

            circuit_data = row.to_dict()

            if existing_circuit:
                # Mise à jour (UPDATE) : Mettre à jour l'objet existant avec les nouvelles données
                for key, value in circuit_data.items():
                    if key in Circuit.model_fields and key not in ['Nom_Circuit', 'Configuration_Piste']:
                        setattr(existing_circuit, key, value)

                session.add(existing_circuit)
                updated_count += 1
            else:
                # Création (INSERT)
                circuit_obj = Circuit(**circuit_data)
                session.add(circuit_obj)
                created_count += 1

            session.commit()

        except ValidationError as e:
            print(f"Erreur de validation à la ligne {index + 2}: {e}")
            session.rollback()
            continue
        except Exception as e:
            session.rollback()
            print(f"Erreur interne à la ligne {index + 2}: {e}")
            continue

    return {
        "message": f"Opération UPSERT terminée.",
        "circuits_mis_a_jour": updated_count,
        "circuits_crees": created_count
    }


@app.get("/courses", response_model=list[Course], summary="Récupérer toutes les courses")
def read_courses(session: SessionDep, offset: int = 0, limit: int = 100):
    """
    Récupère une liste de courses avec pagination. Inclut les détails du circuit.
    """
    # L'utilisation de 'response_model=list[Course]' assure que l'objet 'circuit' est
    # chargé grâce à la relation définie dans le modèle Course.
    courses = session.exec(select(Course).offset(offset).limit(limit)).all()
    return courses


@app.get("/courses/{course_id}", response_model=Course, summary="Récupérer une course par ID")
def read_course_by_id(course_id: int, session: SessionDep):
    """
    Récupère une course spécifique par son identifiant unique.
    """
    course = session.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course non trouvée")
    return course


@app.get("/courses/export", summary="Exporter toutes les courses au format CSV")
async def export_courses(session: SessionDep):
    """
    Récupère toutes les données de la table 'Course', y compris les informations de circuit
    (via une jointure), et les retourne au format CSV.
    """
    try:
        # 1. Récupérer les données avec jointure pour inclure les détails du circuit
        statement = select(Course, Circuit).join(Circuit)
        results = session.exec(statement).all()

        if not results:
            raise HTTPException(status_code=404, detail="Aucune course trouvée pour l'exportation.")

        # 2. Créer une liste de dictionnaires pour le DataFrame
        data = []
        for course, circuit in results:
            course_dict = course.model_dump()

            # Ajouter les détails du circuit et renommer les colonnes
            course_dict['Nom_Circuit'] = circuit.Nom_Circuit
            course_dict['Configuration_Piste'] = circuit.Configuration_Piste

            # Nettoyage des colonnes internes avant d'ajouter à la liste
            del course_dict['id']
            del course_dict['circuit_id']

            data.append(course_dict)

        # 3. Convertir en DataFrame
        df = pd.DataFrame(data)

        # 4. Réordonner les colonnes pour qu'elles aient plus de sens dans le CSV final
        ordered_columns = [
            'Section', 'Pilote', 'Date',
            'Nom_Circuit', 'Configuration_Piste',
            'Kart', 'Note', 'Meilleur_Tour', 'Ecart', 'Tours', 'Humidite'
        ]
        df = df[ordered_columns]

        # 5. Renvoyer le CSV
        return export_data_to_csv_response(df, "export_courses")

    except HTTPException:
        raise  # Reroute l'exception 404
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'exportation des courses : {e}")


@app.put("/courses/import", status_code=status.HTTP_200_OK,
         summary="Mettre à jour/Insérer des courses via CSV (UPSERT) basé sur (Section, Pilote, Date)")
async def upsert_courses_csv(
        file: UploadFile = File(...),
        session: SessionDep = None
):
    """
    Importe et met à jour les données des courses à partir d'un fichier CSV en utilisant
    (Section, Pilote, Date) comme clé logique.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Seuls les fichiers .csv sont acceptés.")

    contents = await file.read()
    buffer = StringIO(contents.decode('utf-8'))

    try:
        df = pd.read_csv(buffer)
        df.columns = [col.strip() for col in df.columns]
        df = df.rename(columns={
            'Meilleur Tour': 'Meilleur_Tour',
            'circuit': 'Nom_Circuit',
            'Piste': 'Configuration_Piste'
        })

        # --- PRÉPARATION DES DONNÉES (CORRECTION FINALE) ---

        # 1. Gérer 'Kart' (Entier optionnel)
        # Remplacement des NaN par -1 avant conversion int, puis retour à None
        df['Kart'] = df['Kart'].fillna(-1).astype(int).replace({-1: None})

        # 2. Gérer 'Humidite' (Float)
        # C'est la colonne qui recevait "Kartland Moissy" à cause du décalage.
        # Maintenant, elle devrait contenir des nombres ou NaN. Remplacer NaN par 0.0
        df['Humidite'] = df['Humidite'].fillna(0.0).astype(float)


        # 4. Gérer les autres entiers (Section, Tours, Note)
        df['Section'] = df['Section'].fillna(0).astype(int)
        df['Note'] = df['Note'].fillna(0).astype(int)

        # 5. Conversion de la Date
        df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce').dt.date

    except Exception as e:
        # Affiche l'erreur complète pour un diagnostic plus facile si elle persiste
        raise HTTPException(status_code=422, detail=f"Erreur de lecture ou de format CSV: {e}")

    updated_count = 0
    created_count = 0
    circuits_uniques = {}  # Cache pour les circuits

    for index, row in df.iterrows():
        try:
            # Clé logique de la course
            section = int(row['Section'])
            pilote = row['Pilote']
            date_course = row['Date']

            # --- Étape 1 : Gérer le Circuit (Identique) ---
            circuit_key = (row['Nom_Circuit'], row['Configuration_Piste'])
            circuit_obj = circuits_uniques.get(circuit_key)

            if not circuit_obj:
                # Chercher ou créer le circuit pour obtenir l'ID de clé étrangère
                statement = select(Circuit).where(
                    Circuit.Nom_Circuit == row['Nom_Circuit'],
                    Circuit.Configuration_Piste == row['Configuration_Piste']
                )
                circuit_obj = session.exec(statement).first()

                if not circuit_obj:
                    # Création du circuit s'il n'existe pas
                    circuit_obj = Circuit(
                        Nom_Circuit=row['Nom_Circuit'],
                        Configuration_Piste=row['Configuration_Piste'],
                        Longueur="N/A", Adresse="N/A"
                    )
                    session.add(circuit_obj)
                    session.commit()
                    session.refresh(circuit_obj)

                circuits_uniques[circuit_key] = circuit_obj

            # --- Étape 2 : Rechercher la Course par Clé Logique ---
            statement = select(Course).where(
                Course.Section == section,
                Course.Pilote == pilote,
                Course.Date == date_course
            )
            existing_course = session.exec(statement).first()

            # Préparation des données de la course
            course_data = row.to_dict()
            course_data['circuit_id'] = circuit_obj.id

            # Nettoyage des champs de circuit (non nécessaires pour l'objet Course)
            del course_data['Nom_Circuit']
            del course_data['Configuration_Piste']

            # Supprimer la clé 'Date' si elle a déjà été convertie en objet date de Python
            # et si elle est implicitement présente dans course_data
            course_data['Date'] = date_course

            if existing_course:
                # UPDATE : Mise à jour de l'enregistrement existant
                for key, value in course_data.items():
                    # Ne pas modifier la clé étrangère (circuit_id) ou l'ID interne
                    if key in Course.model_fields and key not in ['id', 'circuit_id']:
                        setattr(existing_course, key, value)

                session.add(existing_course)
                updated_count += 1
            else:
                # INSERT : Création d'un nouvel enregistrement
                # Assurez-vous que l'ID n'est pas inclus dans le dict si vous l'aviez géré précédemment
                course_obj = Course(**course_data)
                session.add(course_obj)
                created_count += 1

            session.commit()

        except ValidationError as e:
            print(f"Erreur de validation à la ligne {index + 2}: {e.errors()}")
            session.rollback()
            continue
        except Exception as e:
            session.rollback()
            print(f"Erreur interne inattendue à la ligne {index + 2}: {e}")
            continue

    return {
        "message": f"Opération UPSERT (basée sur Section, Pilote, Date) terminée.",
        "courses_mises_a_jour": updated_count,
        "courses_crees": created_count
    }
