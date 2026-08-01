import streamlit as st
import pandas as pd

# 1. Le faux contrat de données (Mock Data)
# C'est ce que Saïd est censé t'envoyer plus tard
MOCK_DATA = {
  "summary_metrics": {
    "total_processed": 200,
    "nps_score": 35,
    "total_promoters": 120,
    "total_passives": 30,
    "total_detractors": 50
  },
  "top_themes": [
    {"theme": "Retard de traitement", "count": 25},
    {"theme": "Problème technique", "count": 15},
    {"theme": "Service client injoignable", "count": 10}
  ],
  "processed_records": [
    {
      "feedback_id": "FBK-001",
      "original_score": 2,
      "assigned_urgency": "Haute",
      "assigned_theme": "Problème technique",
      "rag_verified": True
    },
    {
      "feedback_id": "FBK-002",
      "original_score": 9,
      "assigned_urgency": "Basse",
      "assigned_theme": "Expérience fluide",
      "rag_verified": False
    }
  ]
}

# 2. Construction de l'interface
st.set_page_config(page_title="CloudShift Dashboard", layout="wide")
st.title("☁️ CloudShift - Agentic Analysis Dashboard")

st.markdown("### Métriques Globales (Mockup)")
metrics = MOCK_DATA["summary_metrics"]

# Affichage des KPIs
col1, col2, col3, col4 = st.columns(4)
col1.metric("Tickets Traités", metrics["total_processed"])
col2.metric("Score NPS", metrics["nps_score"])
col3.metric("Promoteurs 🟢", metrics["total_promoters"])
col4.metric("Détracteurs 🔴", metrics["total_detractors"])

st.divider()

# Affichage des thèmes et du tableau
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("### Top Thèmes")
    themes_df = pd.DataFrame(MOCK_DATA["top_themes"])
    st.dataframe(themes_df, use_container_width=True)

with col_right:
    st.markdown("### Derniers Tickets Analysés")
    records_df = pd.DataFrame(MOCK_DATA["processed_records"])
    st.dataframe(records_df, use_container_width=True)