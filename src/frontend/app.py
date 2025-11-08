import streamlit as st
import pandas as pd
from datetime import date
from .src.api_client import KartingAPIClient
from .src.data_analysis import KartingDataAnalyzer
from .src.ui_components import UIComponents
from .src.utils import save_dataframe_to_csv, generate_filename


def main():
    # Configuration de la page Streamlit
    st.set_page_config(
        page_title="Analyse des données de karting",
        page_icon="🏎️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Initialisation des clients et analyseurs
    @st.cache_resource
    def get_api_client():
        return KartingAPIClient(base_url="http://localhost:8000")

    @st.cache_data
    def load_data(_api: KartingAPIClient):
        circuits_data = api.get_circuits()
        courses_data = api.get_courses()
        return circuits_data, courses_data

    # Chargement des données
    api = get_api_client()
    circuits_data, courses_data = load_data(api)
    analyzer = KartingDataAnalyzer(circuits_data, courses_data)

    # Titre de l'application
    st.title("🏎️ Analyse des données de karting")

    # Barre latérale pour la navigation
    with st.sidebar:
        st.header("Navigation")
        menu = [
            "Tableau de bord",
            "Analyse par circuit",
            "Analyse par pilote",
            "Export/Import",
        ]
        choice = st.selectbox("Menu", menu, key="main_menu")

    # --- Tableau de bord ---
    if choice == "Tableau de bord":
        st.header("📊 Tableau de bord global")

        # Affichage des statistiques globales
        global_stats = analyzer.get_global_stats()
        UIComponents.display_global_stats(global_stats)

        # Graphique de comparaison des performances par circuit
        fig = analyzer.plot_circuit_performance_comparison()
        UIComponents.display_plotly_figure(fig, "Comparaison des performances par circuit")

        # Affichage des données brutes (optionnel)
        with st.expander("Voir les données brutes"):
            st.subheader("Circuits")
            UIComponents.display_dataframe(
                pd.DataFrame(circuits_data), "Liste des circuits", "circuits_df"
            )
            st.subheader("Courses")
            UIComponents.display_dataframe(
                pd.DataFrame(courses_data), "Liste des courses", "courses_df"
            )

    # --- Analyse par circuit ---
    elif choice == "Analyse par circuit":
        st.header("🏁 Analyse par circuit")

        # Sélection du circuit
        circuit_id = UIComponents.circuit_selector(pd.DataFrame(circuits_data))

        # Affichage des statistiques du circuit
        circuit_stats = analyzer.get_circuit_performance(circuit_id)
        UIComponents.display_circuit_performance(circuit_stats)

        # Graphique humidité vs performance
        fig = analyzer.plot_humidity_vs_performance(circuit_id)
        UIComponents.display_plotly_figure(fig, "Humidité vs Performance")

        # Affichage des courses du circuit
        circuit_courses = pd.DataFrame(
            [course for course in courses_data if course["circuit_id"] == circuit_id]
        )
        UIComponents.display_dataframe(
            circuit_courses, f"Courses du circuit ID {circuit_id}", "circuit_courses_df"
        )

    # --- Analyse par pilote ---
    elif choice == "Analyse par pilote":
        st.header("👤 Analyse par pilote")

        # Sélection du pilote
        pilot_name = UIComponents.pilot_selector(pd.DataFrame(courses_data))

        # Affichage des statistiques du pilote
        pilot_stats = analyzer.get_pilot_stats(pilot_name)
        UIComponents.display_pilot_stats(pilot_stats)

        # Graphique d'évolution temporelle
        fig = analyzer.plot_pilot_evolution(pilot_name)
        UIComponents.display_plotly_figure(fig, f"Évolution de {pilot_name}")

        # Affichage des courses du pilote
        pilot_courses = pd.DataFrame(
            [course for course in courses_data if course["Pilote"].lower() == pilot_name.lower()]
        )
        UIComponents.display_dataframe(
            pilot_courses, f"Courses de {pilot_name}", "pilot_courses_df"
        )

    # --- Export/Import ---
    elif choice == "Export/Import":
        st.header("📤 Export/Import des données")
        col1, col2 = st.columns(2)
        # Section Export
        with col1:
            UIComponents.display_download_button(
                pd.DataFrame(circuits_data),
                generate_filename("circuits_export", "csv"),
                "Exporter les circuits en CSV",
            )
        with col2:
            UIComponents.display_download_button(
                pd.DataFrame(courses_data),
                generate_filename("courses_export", "csv"),
                "Exporter les courses en CSV",
            )

        # Section Import
        st.subheader("Importer les données")
        col1, col2 = st.columns(2)
        with col1:
            UIComponents.display_import_section(
                lambda file: api.import_circuits_from_csv(file.name), "circuits"
            )
        with col2:
            UIComponents.display_import_section(
                lambda file: api.import_courses_from_csv(file.name), "courses"
            )

    # Pied de page
    st.markdown("---")
    st.markdown(
        """
        **Application d'analyse des données de karting** | Powered by Streamlit & FastAPI
        """
    )

if __name__ == '__main__':
    main()