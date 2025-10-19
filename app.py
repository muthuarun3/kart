import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Analyse Karting",
    page_icon="🏎️",
    layout="wide"
)


# Fonction pour convertir le temps en secondes
def time_to_seconds(time_str):
    if pd.isna(time_str) or time_str == '':
        return None

    time_str = str(time_str).strip()

    # Format min:sec.ms
    if ':' in time_str:
        parts = time_str.split(':')
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    # Format sec.ms
    else:
        return float(time_str)


# Chargement des données
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)

    # Conversion des temps en secondes
    df['Temps_secondes'] = df['Temps (min:sec.ms)'].apply(time_to_seconds)

    # Conversion des dates
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    return df


# Titre principal
st.title("🏎️ Tableau de bord d'analyse Karting")

# Upload du fichier
uploaded_file = 'data.csv'

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Séparation des données Détails et Résumé
    df_details = df[df['Section'] == 'Détails'].copy()
    df_resume = df[df['Section'] == 'Résumé'].copy()

    # Sidebar pour les filtres
    st.sidebar.header("Filtres")

    # Filtre par pilote
    pilotes = df_details['Pilote'].dropna().unique()
    pilote_select = st.sidebar.multiselect(
        "Sélectionner les pilotes",
        options=pilotes,
        default=pilotes
    )

    # Filtre par circuit
    circuits = df_details['Circuit'].dropna().unique()
    circuit_select = st.sidebar.multiselect(
        "Sélectionner les circuits",
        options=circuits,
        default=circuits
    )

    # Filtrage des données
    df_filtered = df_details[
        (df_details['Pilote'].isin(pilote_select)) &
        (df_details['Circuit'].isin(circuit_select))
        ]

    # Métriques principales
    container = st.container(border=True)
    container.header("📊 Vue d'ensemble")

    col1, col2, col3, col4 = container.columns(4)

    with col1:
        st.metric("Nombre de tours", len(df_filtered))

    with col2:
        meilleur_temps = df_filtered['Temps_secondes'].min()
        st.metric("Meilleur temps", f"{meilleur_temps:.3f}s" if pd.notna(meilleur_temps) else "N/A")

    with col3:
        temps_moyen = df_filtered['Temps_secondes'].mean()
        st.metric("Temps moyen", f"{temps_moyen:.3f}s" if pd.notna(temps_moyen) else "N/A")

    with col4:
        nb_pilotes = df_filtered['Pilote'].nunique()
        st.metric("Nombre de pilotes", nb_pilotes)

    # Graphiques
    st.header("📈 Analyses")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Évolution des temps", "Comparaison pilotes", "Comparaison karts", "Distribution", "Résumé"])

    with tab1:
        st.subheader("Évolution des temps par tour")

        if not df_filtered.empty:
            # Ajout d'un numéro de tour
            df_plot = df_filtered.copy()
            df_plot['Numéro_tour'] = df_plot.groupby(['Pilote', 'Circuit', 'Date']).cumcount() + 1

            fig = px.line(
                df_plot,
                x='Numéro_tour',
                y='Temps_secondes',
                color='Pilote',
                markers=True,
                facet_col='Circuit',
                title="Progression des temps de tour",
                labels={'Temps_secondes': 'Temps (secondes)', 'Numéro_tour': 'Numéro de tour'}
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher avec les filtres sélectionnés")

    with tab2:
        st.subheader("Comparaison des performances par pilote")

        if not df_filtered.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Box plot par pilote
                fig = px.box(
                    df_filtered,
                    x='Pilote',
                    y='Temps_secondes',
                    color='Pilote',
                    title="Distribution des temps par pilote",
                    labels={'Temps_secondes': 'Temps (secondes)'}
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Temps moyens par pilote et circuit
                avg_times = df_filtered.groupby(['Pilote', 'Circuit'])['Temps_secondes'].mean().reset_index()
                fig = px.bar(
                    avg_times,
                    x='Pilote',
                    y='Temps_secondes',
                    color='Circuit',
                    barmode='group',
                    title="Temps moyens par pilote et circuit",
                    labels={'Temps_secondes': 'Temps moyen (secondes)'}
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Comparaison des performances par kart")

        # Filtrer uniquement les données avec numéro de kart
        df_karts = df_filtered[df_filtered['Kart'].notna()].copy()

        if not df_karts.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Box plot par kart
                fig = px.box(
                    df_karts,
                    x='Kart',
                    y='Temps_secondes',
                    color='Kart',
                    title="Distribution des temps par kart",
                    labels={'Temps_secondes': 'Temps (secondes)', 'Kart': 'Numéro de kart'}
                )
                fig.update_xaxes(type='category')

                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Temps moyens par kart
                avg_karts = df_karts.groupby('Kart')['Temps_secondes'].mean().reset_index()
                avg_karts = avg_karts.sort_values('Temps_secondes')

                fig = px.bar(
                    avg_karts,
                    x='Kart',
                    y='Temps_secondes',
                    title="Temps moyens par kart (du plus rapide au plus lent)",
                    labels={'Temps_secondes': 'Temps moyen (secondes)', 'Kart': 'Numéro de kart'},
                    color='Temps_secondes',
                    color_continuous_scale='RdYlGn_r'
                )
                fig.update_xaxes(type='category')
                st.plotly_chart(fig, use_container_width=True)

            # Tableau comparatif pilotes/karts
            st.subheader("Performances par pilote et kart")

            pilot_kart_stats = df_karts.groupby(['Pilote', 'Kart']).agg({
                'Temps_secondes': ['count', 'mean', 'min']
            }).round(3)

            pilot_kart_stats.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps']
            pilot_kart_stats = pilot_kart_stats.reset_index()

            fig = px.scatter(
                pilot_kart_stats,
                x='Kart',
                y='Temps moyen',
                size='Nombre de tours',
                color='Pilote',
                title="Performance des pilotes selon les karts",
                labels={'Temps moyen': 'Temps moyen (secondes)', 'Kart': 'Numéro de kart'},
                hover_data=['Meilleur temps']
            )
            fig.update_xaxes(type='category')
            st.plotly_chart(fig, use_container_width=True)

            # Statistiques détaillées par kart
            st.subheader("Statistiques détaillées par kart")

            kart_stats = df_karts.groupby('Kart').agg({
                'Temps_secondes': ['count', 'mean', 'min', 'max', 'std']
            }).round(3)

            kart_stats.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps', 'Temps le plus lent',
                                  'Écart-type']
            kart_stats = kart_stats.sort_values('Temps moyen')
            st.dataframe(kart_stats, use_container_width=True)

            # Heatmap pilote vs kart
            if len(df_karts['Pilote'].unique()) > 1 and len(df_karts['Kart'].unique()) > 1:
                st.subheader("Carte de chaleur : Temps moyens par pilote et kart")

                pivot_data = df_karts.pivot_table(
                    values='Temps_secondes',
                    index='Pilote',
                    columns='Kart',
                    aggfunc='mean'
                )

                fig = px.imshow(
                    pivot_data,
                    labels=dict(x="Numéro de kart", y="Pilote", color="Temps (s)"),
                    color_continuous_scale='RdYlGn_r',
                    title="Temps moyens : plus foncé = plus rapide"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée de kart disponible avec les filtres sélectionnés")

    with tab5:
        st.subheader("Distribution des temps")

        if not df_filtered.empty:
            fig = px.histogram(
                df_filtered,
                x='Temps_secondes',
                color='Pilote',
                nbins=20,
                title="Distribution des temps de tour",
                labels={'Temps_secondes': 'Temps (secondes)'},
                barmode='overlay',
                opacity=0.7
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.subheader("Résumé des performances")

        if not df_resume.empty:
            st.dataframe(df_resume, use_container_width=True)

        # Statistiques détaillées par pilote
        st.subheader("Statistiques détaillées")

        stats = df_filtered.groupby('Pilote').agg({
            'Temps_secondes': ['count', 'mean', 'min', 'max', 'std']
        }).round(3)

        stats.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps', 'Temps le plus lent', 'Écart-type']
        st.dataframe(stats, use_container_width=True)

    # Données brutes
    with st.expander("📋 Voir les données brutes"):
        st.dataframe(df_filtered, use_container_width=True)

        # Export
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Télécharger les données filtrées (CSV)",
            data=csv,
            file_name="donnees_karting_filtrees.csv",
            mime="text/csv"
        )

else:
    st.info("👆 Veuillez uploader le fichier data.csv pour commencer l'analyse")

    # Instructions
    st.markdown("""
    ### Comment utiliser cette application ?

    1. **Uploadez votre fichier CSV** en utilisant le bouton ci-dessus
    2. **Filtrez les données** via la barre latérale (pilotes, circuits)
    3. **Explorez les différents onglets** pour analyser les performances
    4. **Téléchargez les résultats** si nécessaire

    #### Fonctionnalités disponibles :
    - 📊 Métriques clés (nombre de tours, meilleurs temps, moyennes)
    - 📈 Évolution des temps par tour
    - 👥 Comparaison entre pilotes
    - 📉 Distribution statistique des temps
    - 📋 Vue des données brutes et export
    """)