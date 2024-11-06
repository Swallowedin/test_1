import streamlit as st
import time
from datetime import datetime, timedelta

def apply_view_style():
    """Applique le style View Avocats"""
    st.markdown("""
        <style>
            /* Style général */
            .stApp {
                background-color: #f8f9fa;
            }
            
            /* Couleurs View */
            .view-primary {
                color: #2F4F4F !important;
            }
            
            /* Header personnalisé */
            .view-header {
                background-color: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 2rem;
            }
            
            /* Cards */
            .view-card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 10px;
                border-left: 4px solid #2F4F4F;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 1rem;
            }
            
            /* Boutons */
            .stButton>button {
                background-color: #2F4F4F;
                color: white;
                border: none;
                padding: 0.5rem 2rem;
                border-radius: 5px;
                font-weight: 500;
                width: 100%;
            }
            
            .stButton>button:hover {
                background-color: #1a2e2e;
            }
            
            /* Inputs */
            .stTextInput>div>div>input {
                border-radius: 5px;
            }
            
            .stTextArea>div>textarea {
                border-radius: 5px;
            }
            
            /* Select */
            .stSelectbox>div>div {
                border-radius: 5px;
            }
        </style>
    """, unsafe_allow_html=True)

def header():
    """Affiche l'en-tête"""
    st.markdown("""
        <div class="view-header">
            <h1 style="color: #2F4F4F; font-size: 2.5rem; margin-bottom: 1rem;">
                Estim'IA by View Avocats
            </h1>
            <p style="color: #666; font-size: 1.2rem;">
                Estimation gratuite et immédiate de vos prestations juridiques
            </p>
        </div>
    """, unsafe_allow_html=True)

def feature_cards():
    """Affiche les points clés"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class="view-card">
                <h3 style="color: #2F4F4F; margin-bottom: 0.5rem;">⚡ Rapide</h3>
                <p style="color: #666;">Estimation en moins de 2 minutes</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""
            <div class="view-card">
                <h3 style="color: #2F4F4F; margin-bottom: 0.5rem;">✓ Fiable</h3>
                <p style="color: #666;">IA entraînée sur nos prestations</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col3:
        st.markdown("""
            <div class="view-card">
                <h3 style="color: #2F4F4F; margin-bottom: 0.5rem;">🔒 Sans engagement</h3>
                <p style="color: #666;">Simple estimation indicative</p>
            </div>
        """, unsafe_allow_html=True)

def main_form():
    """Affiche le formulaire principal"""
    st.markdown('<div class="view-card">', unsafe_allow_html=True)
    
    st.markdown("""
        <h2 style="color: #2F4F4F; font-size: 1.5rem; margin-bottom: 1.5rem;">
            Décrivez votre situation
        </h2>
    """, unsafe_allow_html=True)
    
    client_type = st.selectbox(
        "Vous êtes :",
        ["Particulier", "Professionnel"]
    )
    
    if client_type == "Professionnel":
        sub_type = st.selectbox(
            "Type d'organisation :",
            ["Entreprise", "Profession libérale", "Association", "Administration"]
        )
        
        if sub_type == "Entreprise":
            st.selectbox(
                "Taille de l'entreprise :",
                ["TPE (< 10 salariés)", "PME (10-250)", "ETI (250-5000)", "Grande entreprise"]
            )
    
    urgency = st.selectbox(
        "Degré d'urgence :",
        ["Normal", "Urgent"]
    )
    
    situation = st.text_area(
        "Votre situation :",
        placeholder="Décrivez votre situation juridique en quelques lignes...",
        height=150
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("Obtenir une estimation gratuite"):
        if situation:
            with st.spinner("Analyse en cours..."):
                # Simulation du temps de traitement
                time.sleep(2)
                display_estimation()
        else:
            st.warning("Veuillez décrire votre situation avant de demander une estimation.")

def display_estimation():
    """Affiche l'estimation"""
    st.markdown("""
        <div class="view-card" style="text-align: center;">
            <h3 style="color: #2F4F4F; margin-bottom: 1rem;">Estimation de la prestation</h3>
            <p style="font-size: 2rem; color: #2F4F4F; font-weight: bold;">À partir de 800 €HT</p>
            <p style="color: #666; font-size: 0.9rem;">Pour consultation juridique • Droit des affaires</p>
        </div>
    """, unsafe_allow_html=True)

def footer():
    """Affiche le pied de page"""
    st.markdown("""
        <div style="text-align: center; padding: 2rem; color: #666; font-size: 0.9rem;">
            <p>© 2024 View Avocats - Cabinet d'avocats en droit des affaires</p>
            <p style="margin-top: 0.5rem;">
                Cette estimation est fournie à titre indicatif et ne constitue pas un engagement contractuel
            </p>
        </div>
    """, unsafe_allow_html=True)

def main():
    # Configuration de la page
    st.set_page_config(
        page_title="Estim'IA - View Avocats",
        page_icon="⚖️",
        layout="wide"
    )
    
    # Application du style
    apply_view_style()
    
    # Affichage des composants
    header()
    feature_cards()
    main_form()
    footer()

if __name__ == "__main__":
    main()
