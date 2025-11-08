import os
import pandas as pd
import logging
from typing import List, Dict, Optional, Union, Tuple
from datetime import datetime, date

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def ensure_directory_exists(directory: str) -> None:
    """
    Crée un répertoire s'il n'existe pas.

    Args:
        directory (str): Chemin du répertoire.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Répertoire créé: {directory}")

def save_dataframe_to_csv(
    df: pd.DataFrame, file_path: str, index: bool = False
) -> None:
    """
    Enregistre un DataFrame dans un fichier CSV.

    Args:
        df (pd.DataFrame): DataFrame à enregistrer.
        file_path (str): Chemin du fichier CSV.
        index (bool): Si True, enregistre l'index.
    """
    ensure_directory_exists(os.path.dirname(file_path))
    df.to_csv(file_path, index=index)
    logger.info(f"Fichier CSV enregistré: {file_path}")

def load_csv_to_dataframe(file_path: str) -> pd.DataFrame:
    """
    Charge un fichier CSV dans un DataFrame.

    Args:
        file_path (str): Chemin du fichier CSV.

    Returns:
        pd.DataFrame: DataFrame chargé.
    """
    df = pd.read_csv(file_path)
    logger.info(f"Fichier CSV chargé: {file_path}")
    return df

def format_time_from_seconds(seconds: float) -> str:
    """
    Formate un temps en secondes en chaîne "MM:SS.sss".

    Args:
        seconds (float): Temps en secondes.

    Returns:
        str: Temps formaté (ex: "1:30.500").
    """
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    milliseconds = (remaining_seconds % 1) * 1000
    return f"{minutes}:{int(remaining_seconds):02d}.{int(milliseconds):03d}"

def parse_date(date_str: str, date_format: str = "%Y-%m-%d") -> date:
    """
    Parse une chaîne de date en objet date.

    Args:
        date_str (str): Chaîne de date.
        date_format (str): Format de la date.

    Returns:
        date: Objet date.
    """
    return datetime.strptime(date_str, date_format).date()

def validate_csv_file(
    file_path: str, required_columns: List[str]
) -> Tuple[bool, Optional[str]]:
    """
    Valide qu'un fichier CSV contient les colonnes requises.

    Args:
        file_path (str): Chemin du fichier CSV.
        required_columns (List[str]): Liste des colonnes requises.

    Returns:
        Tuple[bool, Optional[str]]: (True, None) si valide, (False, message) sinon.
    """
    try:
        df = pd.read_csv(file_path, nrows=1)
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return (
                False,
                f"Colonnes manquantes dans le fichier: {', '.join(missing_columns)}",
            )
        return True, None
    except Exception as e:
        return False, f"Erreur lors de la lecture du fichier: {e}"

def generate_filename(
    prefix: str, extension: str = "csv", timestamp: bool = True
) -> str:
    """
    Génère un nom de fichier avec un timestamp optionnel.

    Args:
        prefix (str): Préfixe du nom de fichier.
        extension (str): Extension du fichier.
        timestamp (bool): Si True, ajoute un timestamp.

    Returns:
        str: Nom de fichier généré.
    """
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S") if timestamp else ""
    return f"{prefix}_{timestamp_str}.{extension}"

def log_api_error(endpoint: str, error: Exception) -> None:
    """
    Log une erreur liée à une requête API.

    Args:
        endpoint (str): Endpoint de l'API concerné.
        error (Exception): Exception levée.
    """
    logger.error(f"Erreur lors de l'appel à {endpoint}: {error}")

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nettoie un DataFrame en supprimant les doublons et les valeurs manquantes.

    Args:
        df (pd.DataFrame): DataFrame à nettoyer.

    Returns:
        pd.DataFrame: DataFrame nettoyé.
    """
    df = df.drop_duplicates()
    df = df.dropna(how="all")
    return df

def convert_dataframe_to_dict_records(df: pd.DataFrame) -> List[Dict]:
    """
    Convertit un DataFrame en liste de dictionnaires (enregistrements).

    Args:
        df (pd.DataFrame): DataFrame à convertir.

    Returns:
        List[Dict]: Liste de dictionnaires.
    """
    return df.to_dict("records")

def filter_dataframe_by_date(
    df: pd.DataFrame, date_column: str, start_date: date, end_date: date
) -> pd.DataFrame:
    """
    Filtre un DataFrame par plage de dates.

    Args:
        df (pd.DataFrame): DataFrame à filtrer.
        date_column (str): Nom de la colonne de date.
        start_date (date): Date de début.
        end_date (date): Date de fin.

    Returns:
        pd.DataFrame: DataFrame filtré.
    """
    mask = (df[date_column] >= pd.to_datetime(start_date)) & (
        df[date_column] <= pd.to_datetime(end_date)
    )
    return df.loc[mask]

def calculate_average_by_group(
    df: pd.DataFrame, group_column: str, value_column: str
) -> pd.DataFrame:
    """
    Calcule la moyenne d'une colonne par groupe.

    Args:
        df (pd.DataFrame): DataFrame à analyser.
        group_column (str): Colonne de regroupement.
        value_column (str): Colonne à moyenniser.

    Returns:
        pd.DataFrame: DataFrame avec les moyennes par groupe.
    """
    return df.groupby(group_column)[value_column].mean().reset_index()
