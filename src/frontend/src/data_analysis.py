import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Optional, Tuple
from datetime import date

class KartingDataAnalyzer:
    """
    Classe pour analyser les données de karting.
    Fournit des méthodes pour calculer des statistiques, générer des graphiques,
    et identifier des tendances ou corrélations.
    """

    def __init__(self, circuits_data: List[Dict], courses_data: List[Dict]):
        """
        Initialise l'analyseur avec les données des circuits et des courses.

        Args:
            circuits_data (List[Dict]): Liste des circuits.
            courses_data (List[Dict]): Liste des courses.
        """
        self.circuits_df = pd.DataFrame(circuits_data)
        self.courses_df = pd.DataFrame(courses_data)

        # Nettoyage des données
        self._clean_data()

    def _clean_data(self) -> None:
        """Nettoie et prépare les données pour l'analyse."""
        # Conversion des colonnes de temps et de date
        if "Meilleur_Tour" in self.courses_df.columns:
            self.courses_df["Meilleur_Tour"] = self.courses_df["Meilleur_Tour"].apply(
                lambda x: self._convert_time_to_seconds(x) if isinstance(x, str) else x
            )
        if "Date" in self.courses_df.columns:
            self.courses_df["Date"] = pd.to_datetime(self.courses_df["Date"])

    def _convert_time_to_seconds(self, time_str: str) -> float:
        """
        Convertit une chaîne de temps (format "MM:SS.sss") en secondes.

        Args:
            time_str (str): Chaîne de temps (ex: "1:30.500").

        Returns:
            float: Temps en secondes.
        """
        try:
            minutes, seconds = time_str.split(":")
            seconds, milliseconds = seconds.split(".")
            return int(minutes) * 60 + int(seconds) + int(milliseconds) / 1000
        except:
            return 0.0

    # --- Statistiques globales ---
    def get_global_stats(self) -> Dict:
        """
        Calcule les statistiques globales pour toutes les courses.

        Returns:
            Dict: Dictionnaire contenant les statistiques (moyennes, min/max, etc.).
        """
        stats = {
            "total_courses": len(self.courses_df),
            "total_circuits": len(self.circuits_df),
            "moyenne_note": self.courses_df["Note"].mean(),
            "moyenne_humidite": self.courses_df["Humidite"].mean(),
            "meilleur_tour_moyen": self.courses_df["Meilleur_Tour"].mean(),
            "moyenne_temps_par_circuit": self._get_average_time_by_circuit(),
        }
        return stats

    def _get_average_time_by_circuit(self) -> Dict:
        """
        Calcule le temps moyen par circuit.

        Returns:
            Dict: Dictionnaire {id_circuit: temps_moyen_en_secondes}.
        """
        return (
            self.courses_df.groupby("circuit_id")["Meilleur_Tour"]
            .mean()
            .to_dict()
        )

    # --- Analyse par circuit ---
    def get_circuit_performance(self, circuit_id: int) -> Dict:
        """
        Analyse les performances pour un circuit donné.

        Args:
            circuit_id (int): ID du circuit.

        Returns:
            Dict: Statistiques pour le circuit (temps moyen, note moyenne, humidité moyenne, etc.).
        """
        circuit_courses = self.courses_df[self.courses_df["circuit_id"] == circuit_id]
        if circuit_courses.empty:
            return {}

        stats = {
            "nom_circuit": self.circuits_df[self.circuits_df["id"] == circuit_id]["Nom_Circuit"].iloc[0],
            "total_courses": len(circuit_courses),
            "moyenne_note": circuit_courses["Note"].mean(),
            "moyenne_humidite": circuit_courses["Humidite"].mean(),
            "meilleur_tour_moyen": circuit_courses["Meilleur_Tour"].mean(),
            "meilleur_tour_record": circuit_courses["Meilleur_Tour"].min(),
            "kart_top_performance": self._get_top_kart_for_circuit(circuit_id),
        }
        return stats

    def _get_top_kart_for_circuit(self, circuit_id: int) -> Dict:
        """
        Identifie le kart le plus performant pour un circuit donné.

        Args:
            circuit_id (int): ID du circuit.

        Returns:
            Dict: Dictionnaire avec le kart le plus performant et ses statistiques.
        """
        circuit_courses = self.courses_df[self.courses_df["circuit_id"] == circuit_id]
        if circuit_courses.empty:
            return {}

        kart_stats = (
            circuit_courses.groupby("Kart")
            .agg(
                moyenne_note=("Note", "mean"),
                moyenne_temps=("Meilleur_Tour", "mean"),
                nombre_courses=("Kart", "count"),
            )
            .sort_values(by=["moyenne_note", "moyenne_temps"], ascending=[False, True])
        )

        top_kart = kart_stats.iloc[0]
        return {
            "kart_id": top_kart.name,
            "moyenne_note": top_kart["moyenne_note"],
            "moyenne_temps": top_kart["moyenne_temps"],
            "nombre_courses": top_kart["nombre_courses"],
        }

    # --- Analyse par pilote ---
    def get_pilot_stats(self, pilot_name: str) -> Dict:
        """
        Calcule les statistiques pour un pilote donné.

        Args:
            pilot_name (str): Nom du pilote.

        Returns:
            Dict: Statistiques du pilote (moyennes, podiums, évolution temporelle).
        """
        pilot_courses = self.courses_df[self.courses_df["Pilote"].str.lower() == pilot_name.lower()]
        if pilot_courses.empty:
            return {}

        stats = {
            "nom_pilote": pilot_name,
            "total_courses": len(pilot_courses),
            "moyenne_note": pilot_courses["Note"].mean(),
            "moyenne_humidite": pilot_courses["Humidite"].mean(),
            "meilleur_tour_moyen": pilot_courses["Meilleur_Tour"].mean(),
            "meilleur_tour_record": pilot_courses["Meilleur_Tour"].min(),
            "taux_podiums": self._calculate_podium_rate(pilot_courses),
            "evolution_temporelle": self._get_pilot_temporal_evolution(pilot_name),
        }
        return stats

    def _calculate_podium_rate(self, pilot_courses: pd.DataFrame) -> float:
        """
        Calcule le taux de podiums pour un pilote (suppose que Note >= 9 = podium).

        Args:
            pilot_courses (pd.DataFrame): DataFrame des courses du pilote.

        Returns:
            float: Taux de podiums (entre 0 et 1).
        """
        if pilot_courses.empty:
            return 0.0
        podium_courses = pilot_courses[pilot_courses["Note"] >= 9]
        return len(podium_courses) / len(pilot_courses)

    def _get_pilot_temporal_evolution(self, pilot_name: str) -> pd.DataFrame:
        """
        Récupère l'évolution temporelle des performances d'un pilote.

        Args:
            pilot_name (str): Nom du pilote.

        Returns:
            pd.DataFrame: DataFrame avec les dates et les notes/temps moyens.
        """
        pilot_courses = self.courses_df[self.courses_df["Pilote"].str.lower() == pilot_name.lower()]
        if pilot_courses.empty:
            return pd.DataFrame()

        evolution = (
            pilot_courses.groupby(pd.Grouper(key="Date", freq="M"))
            .agg(
                moyenne_note=("Note", "mean"),
                moyenne_temps=("Meilleur_Tour", "mean"),
                nombre_courses=("Pilote", "count"),
            )
            .reset_index()
        )
        return evolution

    # --- Visualisations ---
    def plot_circuit_performance_comparison(self) -> go.Figure:
        """
        Génère un graphique comparant les performances moyennes par circuit.

        Returns:
            go.Figure: Graphique Plotly (barres groupées).
        """
        circuit_stats = (
            self.courses_df.groupby("circuit_id")
            .agg(
                moyenne_note=("Note", "mean"),
                moyenne_temps=("Meilleur_Tour", "mean"),
                moyenne_humidite=("Humidite", "mean"),
            )
            .reset_index()
        )

        # Fusion avec les noms de circuits
        circuit_stats = circuit_stats.merge(
            self.circuits_df[["id", "Nom_Circuit"]],
            left_on="circuit_id",
            right_on="id",
            how="left",
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=circuit_stats["Nom_Circuit"],
                y=circuit_stats["moyenne_note"],
                name="Note Moyenne",
            )
        )
        fig.add_trace(
            go.Bar(
                x=circuit_stats["Nom_Circuit"],
                y=circuit_stats["moyenne_temps"],
                name="Temps Moyen (s)",
            )
        )
        fig.update_layout(
            title="Comparaison des performances moyennes par circuit",
            xaxis_title="Circuit",
            yaxis_title="Valeur",
            barmode="group",
        )
        return fig

    def plot_pilot_evolution(self, pilot_name: str) -> go.Figure:
        """
        Génère un graphique de l'évolution temporelle des performances d'un pilote.

        Args:
            pilot_name (str): Nom du pilote.

        Returns:
            go.Figure: Graphique Plotly (lignes).
        """
        evolution = self._get_pilot_temporal_evolution(pilot_name)
        if evolution.empty:
            return go.Figure()

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=evolution["Date"],
                y=evolution["moyenne_note"],
                name="Note Moyenne",
                mode="lines+markers",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=evolution["Date"],
                y=evolution["moyenne_temps"],
                name="Temps Moyen (s)",
                mode="lines+markers",
            )
        )
        fig.update_layout(
            title=f"Évolution des performances de {pilot_name}",
            xaxis_title="Date",
            yaxis_title="Valeur",
        )
        return fig

    def plot_humidity_vs_performance(self, circuit_id: Optional[int] = None) -> go.Figure:
        """
        Génère un scatter plot pour analyser la corrélation entre humidité et performance.

        Args:
            circuit_id (int, optional): Filtrer par circuit.

        Returns:
            go.Figure: Graphique Plotly (scatter plot).
        """
        data = self.courses_df
        if circuit_id:
            data = data[data["circuit_id"] == circuit_id]

        fig = px.scatter(
            data,
            x="Humidite",
            y="Note",
            color="Kart",
            title="Corrélation entre humidité et performance (Note)",
            labels={"Humidite": "Humidité (%)", "Note": "Note"},
        )
        return fig
