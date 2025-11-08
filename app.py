import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.backend.utils import convert_time_to_seconds, convert_seconds_to_time, calculate_metrics, apply_filters

# Configuration de la page
st.set_page_config(
    page_title="Analyse Karting",
    page_icon="🏎️",
    layout="wide"
)

# Titre de l'application
st.title("🏎️ Tableau de bord d'analyse Karting")





# Fonction pour charger et traiter les données
@st.cache_data
def load_data(uploaded_file):
    try:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        # Conversion des colonnes de temps
        df['Temps (min:sec.ms)'] = df['Temps (min:sec.ms)'].apply(convert_time_to_seconds)
        df['Meilleur Tour'] = df['Meilleur Tour'].apply(convert_time_to_seconds)
        # Conversion des dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {e}")
        return None



# Fonction pour afficher les métriques
def display_metrics(num_sessions, best_lap, avg_time):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre de sessions", num_sessions)
    with col2:
        st.metric("Meilleur tour", convert_seconds_to_time(best_lap))
    with col3:
        st.metric("Temps moyen", convert_seconds_to_time(avg_time))

# Fonction pour afficher les filtres
def display_filters(df):
    if df is None or df.empty:
        return None, None, None, None

    # Filtre pilotes
    pilots = df['Pilote'].unique()
    selected_pilots = st.multiselect("Pilotes", pilots, default=pilots)

    # Filtre circuit
    circuits = df['Circuit'].unique()
    selected_circuit = st.selectbox("Circuit", circuits, index=0)

    # Filtre humidité
    min_humidity, max_humidity = st.slider(
        "Humidité (%)",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0)
    )

    return selected_pilots, selected_circuit, min_humidity, max_humidity



# Fonction pour afficher l'onglet Évolution des temps
def display_time_evolution_tab(filtered_df):
    if filtered_df.empty:
        st.warning("Aucune donnée à afficher avec les filtres sélectionnés.")
        return

    # Graphique d'évolution des temps
    fig = px.line(
        filtered_df,
        x='Date',
        y='Temps (min:sec.ms)',
        color='Pilote',
        title="Évolution des temps par pilote",
        labels={'Temps (min:sec.ms)': 'Temps (secondes)', 'Date': 'Date'}
    )
    fig.update_traces(mode='lines+markers')
    st.plotly_chart(fig, use_container_width=True)

    # Tableau des données résumé
    st.subheader("Tableau des données résumé")
    summary_df = filtered_df[filtered_df['Section'] == 'Résumé']
    st.dataframe(summary_df)

    # Statistiques détaillées par pilote
    st.subheader("Statistiques détaillées par pilote")
    stats_df = filtered_df.groupby('Pilote').agg(
        Nombre_de_tours=('Tours', 'sum'),
        Temps_moyen=('Temps (min:sec.ms)', 'mean'),
        Meilleur_temps=('Temps (min:sec.ms)', 'min'),
        Temps_le_plus_lent=('Temps (min:sec.ms)', 'max'),
        Écart_type=('Temps (min:sec.ms)', 'std')
    ).round(3)
    st.dataframe(stats_df)

# Fonction pour afficher l'onglet Comparaison pilotes
def display_pilot_comparison_tab(filtered_df):
    if filtered_df.empty:
        st.warning("Aucune donnée à afficher avec les filtres sélectionnés.")
        return

    # Box plot des temps par pilote
    fig = px.box(
        filtered_df,
        x='Pilote',
        y='Temps (min:sec.ms)',
        title="Distribution des temps par pilote",
        labels={'Temps (min:sec.ms)': 'Temps (secondes)'}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Cartes métriques par pilote et circuit
    st.subheader("Temps moyens par pilote et circuit")
    metric_df = filtered_df.groupby(['Pilote', 'Circuit']).agg(
        Temps_moyen=('Temps (min:sec.ms)', 'mean')
    ).reset_index()
    for pilot in metric_df['Pilote'].unique():
        pilot_data = metric_df[metric_df['Pilote'] == pilot]
        for _, row in pilot_data.iterrows():
            st.metric(
                label=f"{row['Pilote']} - {row['Circuit']}",
                value=convert_seconds_to_time(row['Temps_moyen'])
            )

# Fonction pour afficher l'onglet Comparaison karts
def display_kart_comparison_tab(filtered_df):
    if filtered_df.empty:
        st.warning("Aucune donnée à afficher avec les filtres sélectionnés.")
        return

    if 'Kart' not in filtered_df.columns or filtered_df['Kart'].isna().all():
        st.warning("Aucune donnée de kart disponible.")
        return

    # Calcul des notes et catégories pour les karts
    kart_stats = filtered_df.groupby('Kart').agg(
        Nombre_de_tours=('Tours', 'sum'),
        Temps_moyen=('Temps (min:sec.ms)', 'mean'),
        Meilleur_temps=('Temps (min:sec.ms)', 'min'),
        Temps_le_plus_lent=('Temps (min:sec.ms)', 'max'),
        Écart_type=('Temps (min:sec.ms)', 'std')
    ).sort_values('Temps_moyen')

    # Calcul des notes (100% = meilleur kart)
    kart_stats['Note'] = 100 * (1 - (kart_stats['Temps_moyen'] - kart_stats['Temps_moyen'].min()) /
                                (kart_stats['Temps_moyen'].max() - kart_stats['Temps_moyen'].min()))
    kart_stats['Catégorie'] = pd.cut(
        kart_stats['Note'],
        bins=[-float('inf'), 30, 70, float('inf')],
        labels=['🔴 pas ouf', '🟡 mid', '🟢 au top']
    )
    kart_stats = kart_stats.sort_values('Note', ascending=False)

    # Tableau des karts
    st.subheader("Classement des karts")
    kart_table = kart_stats[['Nombre_de_tours', 'Temps_moyen', 'Note', 'Catégorie']].reset_index()
    kart_table['Temps_moyen'] = kart_table['Temps_moyen'].apply(convert_seconds_to_time)
    kart_table['Note'] = kart_table['Note'].round(1)
    st.dataframe(kart_table)

    # Graphique en barres des temps moyens par kart
    fig = px.bar(
        kart_stats.reset_index(),
        x='Kart',
        y='Temps_moyen',
        title="Temps moyens par kart (du plus rapide au plus lent)",
        labels={'Temps_moyen': 'Temps moyen (secondes)', 'Kart': 'Numéro de kart'},
        color='Temps_moyen',
        color_continuous_scale='RdYlGn_r'
    )
    st.plotly_chart(fig, use_container_width=True)

    # Heatmap pilotes vs karts
    if filtered_df['Pilote'].nunique() >= 2 and filtered_df['Kart'].nunique() >= 2:
        st.subheader("Heatmap: Temps moyens par pilote et kart")
        heatmap_df = filtered_df.groupby(['Pilote', 'Kart']).agg(
            Temps_moyen=('Temps (min:sec.ms)', 'mean')
        ).reset_index()
        heatmap_df = heatmap_df.pivot(index='Pilote', columns='Kart', values='Temps_moyen')
        fig = go.Figure(data=go.Heatmap(
            z=heatmap_df.values,
            x=heatmap_df.columns,
            y=heatmap_df.index,
            colorscale='Viridis',
            colorbar=dict(title='Temps (secondes)')
        ))
        fig.update_layout(title="Temps moyens par pilote et kart (plus foncé = plus rapide)")
        st.plotly_chart(fig, use_container_width=True)

# Fonction pour afficher les données brutes
def display_raw_data(filtered_df):
    with st.expander("📋 Voir les données brutes"):
        st.dataframe(filtered_df)
        if not filtered_df.empty:
            csv = filtered_df.to_csv(index=False, encoding='utf-8')
            st.download_button(
                label="Télécharger les données filtrées",
                data=csv,
                file_name="donnees_karting_filtrees.csv",
                mime="text/csv"
            )

# Upload du fichier
uploaded_file = 'src/assets/data.csv'  # Pour le test local, remplacer par st.file_uploader("Téléverser un fichier CSV", type=["csv"])

if uploaded_file is not None:
    # Chargement des données
    df = load_data(uploaded_file)

    if df is not None and not df.empty:
        # Affichage des filtres
        selected_pilots, selected_circuit, min_humidity, max_humidity = display_filters(df)

        # Application des filtres
        filtered_df = apply_filters(df, selected_pilots, selected_circuit, min_humidity, max_humidity)

        # Calcul des métriques
        num_sessions, best_lap, avg_time = calculate_metrics(filtered_df)

        # Affichage des métriques
        display_metrics(num_sessions, best_lap, avg_time)

        # Onglets d'analyse
        tab1, tab2, tab3 = st.tabs(["📈 Évolution des temps", "👥 Comparaison pilotes", "🏎️ Comparaison karts"])

        with tab1:
            display_time_evolution_tab(filtered_df)

        with tab2:
            display_pilot_comparison_tab(filtered_df)

        with tab3:
            display_kart_comparison_tab(filtered_df)

        # Affichage des données brutes
        display_raw_data(filtered_df)
    else:
        st.warning("Le fichier chargé est vide ou invalide.")
else:
    st.info("Veuillez téléverser un fichier CSV pour commencer l'analyse.")
    st.markdown("""
    ### Instructions
    - Téléchargez un fichier CSV contenant vos données de karting.
    - Le fichier doit contenir les colonnes obligatoires: **Section, Pilote, Date, Circuit, Meilleur Tour**.
    - Les colonnes optionnelles sont: **Temps (min:sec.ms), Kart, Note, Ecart, Tours, Humidite**.
    - Une fois le fichier chargé, vous pourrez filtrer et analyser vos données.
    """)
