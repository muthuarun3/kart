import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Optional, Callable, Tuple
from datetime import date

from streamlit import container


class UIComponents:
    """
    Classe pour gérer les composants UI réutilisables dans Streamlit.
    Fournit des méthodes pour afficher des tableaux, des graphiques, des filtres, etc.
    """

    @staticmethod
    def display_global_stats(stats: Dict) -> None:
        """
        Affiche les statistiques globales dans un format clair et visuel.

        Args:
            stats (Dict): Dictionnaire de statistiques globales.
        """
        container = st.container(border=True)
        container.header("Statistiques Globales")

        col1, col2, col3, col4 = container.columns(4)
        with col1:
            st.metric("Nombre de circuits", stats["total_circuits"])
        with col2:
            st.metric("Nombre de courses", stats["total_courses"])
        with col3:
            st.metric("Note moyenne", f"{stats['moyenne_note']:.2f}")
        with col4:
            st.metric("Humidité moyenne", f"{stats['moyenne_humidite']:.1f}%")

        container.subheader("Temps moyen par circuit (en secondes)")
        for circuit_id, temps in stats["moyenne_temps_par_circuit"].items():
            container.write(f"- Circuit {circuit_id}: {temps:.2f} s")

    @staticmethod
    def display_circuit_performance(circuit_stats: Dict) -> None:
        """
        Affiche les performances d'un circuit donné.

        Args:
            circuit_stats (Dict): Statistiques pour un circuit.
        """
        container = st.container(border=True)
        if not circuit_stats:
            container.warning("Aucune donnée disponible pour ce circuit.")
            return

        container.header(f"🏁 Performance du circuit: {circuit_stats['nom_circuit']}")

        col1, col2, col3 = container.columns(3)
        with col1:
            st.metric("Nombre de courses", circuit_stats["total_courses"])
        with col2:
            st.metric("Note moyenne", f"{circuit_stats['moyenne_note']:.2f}")
        with col3:
            st.metric("Humidité moyenne", f"{circuit_stats['moyenne_humidite']:.1f}%")

        container.subheader("Meilleur tour")
        container.write(f"- Moyen: {circuit_stats['meilleur_tour_moyen']:.2f} s")
        container.write(f"- Record: {circuit_stats['meilleur_tour_record']:.2f} s")

        container.subheader("Kart le plus performant")
        kart = circuit_stats["kart_top_performance"]
        container.write(f"- **Kart ID {kart['kart_id']}**")
        container.write(f"  - Note moyenne: {kart['moyenne_note']:.2f}")
        container.write(f"  - Temps moyen: {kart['moyenne_temps']:.2f} s")
        container.write(f"  - Nombre de courses: {kart['nombre_courses']}")

    @staticmethod
    def display_pilot_stats(pilot_stats: Dict) -> None:
        """
        Affiche les statistiques d'un pilote donné.

        Args:
            pilot_stats (Dict): Statistiques pour un pilote.
        """
        container = st.container(border=True)
        if not pilot_stats:
            container.warning("Aucune donnée disponible pour ce pilote.")
            return

        container.header(f"🚀 Statistiques du pilote: {pilot_stats['nom_pilote']}")

        col1, col2, col3, col4 = container.columns(4)
        with col1:
            st.metric("Courses", pilot_stats["total_courses"])
        with col2:
            st.metric("Note moyenne", f"{pilot_stats['moyenne_note']:.2f}")
        with col3:
            st.metric("Humidité moyenne", f"{pilot_stats['moyenne_humidite']:.1f}%")
        with col4:
            st.metric("Taux de podiums", f"{pilot_stats['taux_podiums']:.0%}")

        container.subheader("Meilleur tour")
        container.write(f"- Moyen: {pilot_stats['meilleur_tour_moyen']:.2f} s")
        container.write(f"- Record: {pilot_stats['meilleur_tour_record']:.2f} s")

        container.subheader("Évolution temporelle")
        evolution_df = pilot_stats["evolution_temporelle"]
        if not evolution_df.empty:
            container.line_chart(evolution_df.set_index("Date")[["moyenne_note", "moyenne_temps"]])
        else:
            container.warning("Aucune donnée d'évolution disponible.")

    @staticmethod
    def display_dataframe(df: pd.DataFrame, title: str, key: str) -> None:
        """
        Affiche un DataFrame avec des options de tri et de filtrage.

        Args:
            df (pd.DataFrame): DataFrame à afficher.
            title (str): Titre de la section.
            key (str): Clé unique pour le composant.
        """
        container = st.container(border=True)
        container.subheader(title)
        container.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            key=key,
        )

    @staticmethod
    def display_plotly_figure(fig: go.Figure, title: str) -> None:
        """
        Affiche une figure Plotly dans Streamlit.

        Args:
            fig (go.Figure): Figure Plotly à afficher.
            title (str): Titre de la section.
        """
        container = st.container(border=True)
        container.subheader(title)
        container.plotly_chart(fig, use_container_width=True)

    @staticmethod
    def circuit_selector(circuits_df: pd.DataFrame) -> int:
        """
        Affiche un sélecteur de circuit et retourne l'ID sélectionné.

        Args:
            circuits_df (pd.DataFrame): DataFrame des circuits.

        Returns:
            int: ID du circuit sélectionné.
        """
        container = st.container(border=True)
        circuit_options = {
            row["Nom_Circuit"]: row["id"] for _, row in circuits_df.iterrows()
        }
        selected_circuit_name = container.selectbox(
            "Sélectionnez un circuit:",
            options=list(circuit_options.keys()),
            key="circuit_selector",
        )
        return circuit_options[selected_circuit_name]

    @staticmethod
    def pilot_selector(courses_df: pd.DataFrame) -> str:
        """
        Affiche un sélecteur de pilote et retourne le nom sélectionné.

        Args:
            courses_df (pd.DataFrame): DataFrame des courses.

        Returns:
            str: Nom du pilote sélectionné.
        """
        container = st.container(border=True)
        pilot_options = courses_df["Pilote"].unique()
        selected_pilot = container.selectbox(
            "Sélectionnez un pilote:",
            options=pilot_options,
            key="pilot_selector",
        )
        return selected_pilot

    @staticmethod
    def date_range_selector() -> Tuple[date, date]:
        """
        Affiche un sélecteur de plage de dates.

        Returns:
            Tuple[date, date]: Dates de début et de fin sélectionnées.
        """
        container = st.container(border=True)
        today = date.today()
        start_date = container.date_input(
            "Date de début:",
            value=date(today.year, 1, 1),
            min_value=date(2020, 1, 1),
            max_value=today,
            key="start_date",
        )
        end_date = container.date_input(
            "Date de fin:",
            value=today,
            min_value=date(2020, 1, 1),
            max_value=today,
            key="end_date",
        )
        return start_date, end_date

    @staticmethod
    def display_download_button(
            data: pd.DataFrame, filename: str, label: str, mime: str = "text/csv"
    ) -> None:
        """
        Affiche un bouton de téléchargement pour un DataFrame au format CSV.

        Args:
            data (pd.DataFrame): DataFrame à exporter.
            filename (str): Nom du fichier à télécharger.
            label (str): Libellé du bouton.
            mime (str): Type MIME du fichier (par défaut "text/csv").
        """
        container = st.container(border=True)
        csv = data.to_csv(index=False).encode("utf-8")
        container.download_button(
            label=label,
            data=csv,
            file_name=filename,
            mime=mime,
        )

    @staticmethod
    def display_export_button(export_function: Callable, filename: str, label: str) -> None:
        """
        Affiche un bouton d'export et déclenche la fonction d'export.

        Args:
            export_function (Callable): Fonction à appeler pour l'export.
            filename (str): Nom du fichier à exporter.
            label (str): Libellé du bouton.
        """
        container = st.container(border=True)

        if container.button(label):
            export_function(filename)
            container.success(f"Fichier {filename} exporté avec succès !")

    @staticmethod
    def display_import_section(import_function: Callable, file_type: str) -> None:
        """
        Affiche une section pour importer un fichier.

        Args:
            import_function (Callable): Fonction à appeler pour l'import.
            file_type (str): Type de fichier ("circuits" ou "courses").
        """
        container = st.container(border=True)
        container.subheader(f"Importer des {file_type}")
        uploaded_file = container.file_uploader(
            f"Sélectionnez un fichier CSV pour les {file_type}:",
            type=["csv"],
            key=f"import_{file_type}",
        )
        if uploaded_file:
            if container.button(f"Importer les {file_type}"):
                import_function(uploaded_file)
                container.success(f"Fichier {uploaded_file.name} importé avec succès !")
