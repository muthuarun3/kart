import io

import numpy as np

import pandas as pd

from starlette.responses import StreamingResponse


# Fonction pour convertir le temps en secondes
def convert_time_to_seconds(time_str):
    if pd.isna(time_str):
        return np.nan
    try:
        if ":" in time_str:
            minutes, rest = time_str.split(":")
            seconds, milliseconds = rest.split(".")
            return float(minutes) * 60 + float(seconds) + float(milliseconds) / 1000
        else:
            seconds, milliseconds = time_str.split(".")
            return float(seconds) + float(milliseconds) / 1000
    except:
        return np.nan


# Fonction pour convertir les secondes en format min:sec.ms
def convert_seconds_to_time(seconds):
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    milliseconds = (remaining_seconds % 1) * 1000
    return f"{minutes}:{int(remaining_seconds):02d}.{int(milliseconds):03d}"


# Fonction pour calculer les métriques principales
def calculate_metrics(df):
    if df.empty:
        return None, None, None
    # Nombre de sessions
    num_sessions = df['Date'].nunique()
    # Meilleur tour
    best_lap = df['Meilleur Tour'].min()
    # Temps moyen
    avg_time = df['Temps (min:sec.ms)'].mean()
    return num_sessions, best_lap, avg_time


# Fonction pour appliquer les filtres
def apply_filters(df, selected_pilots, selected_circuit, min_humidity, max_humidity):
    if df is None or df.empty:
        return df
    filtered_df = df[
        (df['Pilote'].isin(selected_pilots)) &
        (df['Circuit'] == selected_circuit) &
        (df['Humidite'] >= min_humidity) &
        (df['Humidite'] <= max_humidity)
        ]
    return filtered_df


# --- NOUVELLE FONCTION D'EXPORTATION ---
def export_data_to_csv_response(df: pd.DataFrame, filename: str) -> StreamingResponse:
    """
    Convertit un DataFrame Pandas en une réponse de streaming CSV.
    """
    stream = io.StringIO()
    # Le 'index=False' est crucial pour ne pas inclure l'index de Pandas dans le CSV
    df.to_csv(stream, index=False, sep=',')

    # Créer un générateur pour le StreamingResponse
    response = StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
    return response
