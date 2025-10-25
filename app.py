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

    # Conversion des temps en secondes (Meilleur Tour)
    df['Temps_secondes'] = df['Meilleur Tour'].apply(time_to_seconds)

    # Conversion des dates
    df['Date'] = pd.to_datetime(df['Date'], format='%d/%m/%Y', errors='coerce')

    # Conversion de l'humidité en numérique
    df['Humidité'] = pd.to_numeric(df['Humidité'], errors='coerce')

    # Conversion du numéro de kart en string pour traitement catégoriel
    df['Kart'] = df['Kart'].astype(str).replace('nan', '')

    return df


# Titre principal
st.title("🏎️ Tableau de bord d'analyse Karting")

# Upload du fichier
uploaded_file = st.file_uploader("Charger le fichier CSV", type=['csv'])

if uploaded_file is not None:
    df = load_data(uploaded_file)

    # Sidebar pour les filtres
    st.sidebar.header("Filtres")

    # Filtre par pilote
    pilotes = df['Pilote'].dropna().unique()
    pilote_select = st.sidebar.multiselect(
        "Sélectionner les pilotes",
        options=pilotes,
        default=pilotes
    )

    # Filtre par circuit
    circuits = df['Circuit'].dropna().unique()
    circuit_select = st.sidebar.multiselect(
        "Sélectionner les circuits",
        options=circuits,
        default=circuits
    )

    # Filtre par date
    dates = sorted(df['Date'].dropna().unique())
    if len(dates) > 0:
        date_select = st.sidebar.multiselect(
            "Sélectionner les dates",
            options=[d.strftime('%d/%m/%Y') for d in dates],
            default=[d.strftime('%d/%m/%Y') for d in dates]
        )
        date_select_dt = pd.to_datetime(date_select, format='%d/%m/%Y')
    else:
        date_select_dt = []

    # Filtrage des données
    df_filtered = df[
        (df['Pilote'].isin(pilote_select)) &
        (df['Circuit'].isin(circuit_select)) &
        (df['Date'].isin(date_select_dt))
        ].copy()

    # Métriques principales
    container = st.container(border=True)
    container.header("📊 Vue d'ensemble")

    col1, col2, col3, col4 = container.columns(4)

    with col1:
        st.metric("Nombre de sessions", len(df_filtered))

    with col2:
        meilleur_temps = df_filtered['Temps_secondes'].min()
        if pd.notna(meilleur_temps):
            mins = int(meilleur_temps // 60)
            secs = meilleur_temps % 60
            if mins > 0:
                st.metric("Meilleur tour", f"{mins}:{secs:06.3f}")
            else:
                st.metric("Meilleur tour", f"{secs:.3f}s")
        else:
            st.metric("Meilleur tour", "N/A")

    with col3:
        temps_moyen = df_filtered['Temps_secondes'].mean()
        if pd.notna(temps_moyen):
            mins = int(temps_moyen // 60)
            secs = temps_moyen % 60
            if mins > 0:
                st.metric("Temps moyen", f"{mins}:{secs:06.3f}")
            else:
                st.metric("Temps moyen", f"{secs:.3f}s")
        else:
            st.metric("Temps moyen", "N/A")

    with col4:
        nb_dates = df_filtered['Date'].nunique()
        st.metric("Nombre de sessions", nb_dates)

    # Graphiques
    st.header("📈 Analyses")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Évolution temporelle", "Comparaison pilotes", "Impact humidité", "Comparaison karts", "Statistiques"]
    )

    with tab1:
        st.subheader("Évolution des performances dans le temps")

        if not df_filtered.empty:
            df_plot = df_filtered.sort_values('Date').copy()

            fig = px.scatter(
                df_plot,
                x='Date',
                y='Temps_secondes',
                color='Pilote',
                size='Humidité',
                hover_data=['Circuit', 'Kart', 'Note', 'Humidité'],
                title="Évolution des meilleurs tours (taille = humidité)",
                labels={'Temps_secondes': 'Temps (secondes)'}
            )

            # Ajouter une ligne de tendance pour chaque pilote
            for pilote in df_plot['Pilote'].unique():
                df_pilote = df_plot[df_plot['Pilote'] == pilote].sort_values('Date')
                fig.add_trace(go.Scatter(
                    x=df_pilote['Date'],
                    y=df_pilote['Temps_secondes'],
                    mode='lines',
                    name=f'{pilote} (tendance)',
                    line=dict(dash='dash'),
                    showlegend=True
                ))

            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            # Graphique par circuit
            st.subheader("Évolution par circuit")
            fig = px.line(
                df_plot,
                x='Date',
                y='Temps_secondes',
                color='Pilote',
                facet_col='Circuit',
                markers=True,
                title="Progression par circuit",
                labels={'Temps_secondes': 'Temps (secondes)'}
            )
            fig.update_layout(height=400)
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

            # Tableau comparatif
            st.subheader("Statistiques par pilote et circuit")
            stats_pilote = df_filtered.groupby(['Pilote', 'Circuit']).agg({
                'Temps_secondes': ['count', 'mean', 'min', 'max']
            }).round(3)
            stats_pilote.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps', 'Temps le plus lent']
            st.dataframe(stats_pilote, use_container_width=True)

    with tab3:
        st.subheader("Impact de l'humidité sur les performances")

        df_humidity = df_filtered[df_filtered['Humidité'].notna()].copy()

        if not df_humidity.empty:
            col1, col2 = st.columns(2)

            with col1:
                # Scatter plot temps vs humidité
                fig = px.scatter(
                    df_humidity,
                    x='Humidité',
                    y='Temps_secondes',
                    color='Pilote',
                    trendline="ols",
                    title="Relation entre humidité et temps de tour",
                    labels={'Temps_secondes': 'Temps (secondes)', 'Humidité': 'Humidité (%)'},
                    hover_data=['Date', 'Circuit', 'Kart']
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Box plot par niveau d'humidité
                df_humidity['Niveau_humidité'] = pd.cut(
                    df_humidity['Humidité'],
                    bins=[-0.1, 0.1, 0.5, 1.0],
                    labels=['Sec (0-0.1)', 'Moyen (0.1-0.5)', 'Humide (0.5-1.0)']
                )

                fig = px.box(
                    df_humidity,
                    x='Niveau_humidité',
                    y='Temps_secondes',
                    color='Pilote',
                    title="Performance selon le niveau d'humidité",
                    labels={'Temps_secondes': 'Temps (secondes)', 'Niveau_humidité': 'Conditions'}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Analyse par pilote et humidité
            st.subheader("Performance moyenne par pilote selon les conditions")
            humidity_stats = df_humidity.groupby(['Pilote', 'Niveau_humidité'])['Temps_secondes'].agg(
                ['mean', 'count']).round(3)
            humidity_stats.columns = ['Temps moyen (s)', 'Nombre de tours']
            st.dataframe(humidity_stats, use_container_width=True)

            # Heatmap pilote vs humidité
            if len(df_humidity['Pilote'].unique()) > 1:
                st.subheader("Carte de chaleur : Performance selon l'humidité")
                pivot_humidity = df_humidity.pivot_table(
                    values='Temps_secondes',
                    index='Pilote',
                    columns='Niveau_humidité',
                    aggfunc='mean'
                )

                fig = px.imshow(
                    pivot_humidity,
                    labels=dict(x="Niveau d'humidité", y="Pilote", color="Temps (s)"),
                    color_continuous_scale='RdYlGn_r',
                    title="Temps moyens selon les conditions"
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée d'humidité disponible")

    with tab4:
        st.subheader("Comparaison des performances par kart")

        df_karts = df_filtered[df_filtered['Kart'] != ''].copy()

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
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Temps moyens par kart avec notation
                avg_karts = df_karts.groupby(['Kart', 'Note'])['Temps_secondes'].mean().reset_index()
                avg_karts = avg_karts.sort_values('Temps_secondes')

                fig = px.bar(
                    avg_karts,
                    x='Kart',
                    y='Temps_secondes',
                    color='Note',
                    title="Temps moyens par kart et notation",
                    labels={'Temps_secondes': 'Temps moyen (secondes)', 'Kart': 'Numéro de kart'},
                )
                st.plotly_chart(fig, use_container_width=True)

            # Statistiques détaillées par kart
            st.subheader("Statistiques détaillées par kart")
            kart_stats = df_karts.groupby(['Kart', 'Note']).agg({
                'Temps_secondes': ['count', 'mean', 'min'],
                'Pilote': lambda x: ', '.join(x.unique())
            }).round(3)
            kart_stats.columns = ['Nombre d\'utilisations', 'Temps moyen', 'Meilleur temps', 'Pilotes']
            kart_stats = kart_stats.sort_values('Temps moyen')
            st.dataframe(kart_stats, use_container_width=True)

            # Analyse par pilote et kart
            st.subheader("Performance par pilote selon le kart")
            pilot_kart = df_karts.groupby(['Pilote', 'Kart']).agg({
                'Temps_secondes': ['count', 'mean', 'min']
            }).round(3)
            pilot_kart.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps']
            st.dataframe(pilot_kart, use_container_width=True)
        else:
            st.info("Aucune donnée de kart disponible")

    with tab5:
        st.subheader("Statistiques globales")

        col1, col2 = st.columns(2)

        with col1:
            # Statistiques par pilote
            st.write("**Par pilote**")
            stats_pilote = df_filtered.groupby('Pilote').agg({
                'Temps_secondes': ['count', 'mean', 'min', 'max', 'std']
            }).round(3)
            stats_pilote.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps', 'Temps le plus lent',
                                    'Écart-type']
            st.dataframe(stats_pilote, use_container_width=True)

        with col2:
            # Statistiques par circuit
            st.write("**Par circuit**")
            stats_circuit = df_filtered.groupby('Circuit').agg({
                'Temps_secondes': ['count', 'mean', 'min', 'max']
            }).round(3)
            stats_circuit.columns = ['Nombre de tours', 'Temps moyen', 'Meilleur temps', 'Temps le plus lent']
            st.dataframe(stats_circuit, use_container_width=True)

        # Distribution des notations
        st.subheader("Distribution des notations de kart")
        df_notes = df_filtered[df_filtered['Note'].notna()]
        if not df_notes.empty:
            note_counts = df_notes.groupby(['Pilote', 'Note']).size().reset_index(name='count')
            fig = px.bar(
                note_counts,
                x='Note',
                y='count',
                color='Pilote',
                barmode='group',
                title="Répartition des notations par pilote",
                labels={'count': 'Nombre de tours', 'Note': 'Notation du kart'}
            )
            st.plotly_chart(fig, use_container_width=True)

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
    st.info("👆 Veuillez uploader un fichier CSV pour commencer l'analyse")

    st.markdown("""
    ### Format attendu du fichier CSV

    Le fichier doit contenir les colonnes suivantes :
    - **Section** : Numéro de session
    - **Pilote** : Nom du pilote
    - **Date** : Date de la session (format JJ/MM/AAAA)
    - **Circuit** : Nom du circuit (Court/Long)
    - **Temps (min:sec.ms)** : Temps global (optionnel)
    - **Kart** : Numéro du kart
    - **Note** : Notation du kart (*, **, ***)
    - **Meilleur Tour** : Temps du meilleur tour (format mm:ss.ms ou ss.ms)
    - **Humidité** : Niveau d'humidité (0 à 1)

    ### Fonctionnalités disponibles
    - 📊 Métriques clés et vue d'ensemble
    - 📈 Évolution temporelle des performances
    - 👥 Comparaison détaillée entre pilotes
    - 🌧️ Analyse de l'impact de l'humidité
    - 🏎️ Comparaison des performances par kart
    - 📉 Statistiques complètes et distribution
    """)