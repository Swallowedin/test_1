import streamlit as st
from openai import OpenAI
import os
import importlib.util
import json
import logging
from typing import Tuple, Dict, Any

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration du client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def load_py_module(file_path: str, module_name: str):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Erreur lors du chargement du module {module_name}: {e}")
        return None

# Chargement des modules
prestations = load_py_module('./prestations-heures.py', 'prestations_heures').get_prestations()
tarifs = load_py_module('./tarifs-prestations.py', 'tarifs_prestations').get_tarifs()
instructions = load_py_module('./chatbot-instructions.py', 'consignes_chatbot').get_chatbot_instructions()

def analyze_question(question: str, client_type: str, urgency: str) -> Tuple[str, str]:
    options = [f"{domaine}: {', '.join(prestations_domaine.keys())}" for domaine, prestations_domaine in prestations.items()]
    prompt = f"""Analysez la question suivante et identifiez le domaine juridique et la prestation la plus pertinente.

Question : {question}
Type de client : {client_type}
Degré d'urgence : {urgency}

Options de domaines et prestations :
{' '.join(options)}

Répondez avec le domaine et la prestation la plus pertinente, séparés par une virgule."""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": prompt}
        ]
    )
    
    answer = response.choices[0].message.content.strip()
    return answer.split(',', 1) if ',' in answer else (answer, "prestation générale")

def calculate_estimate(domaine: str, prestation: str, urgency: str) -> Tuple[int, int, list, Dict[str, Any]]:
    try:
        heures = prestations.get(domaine, {}).get(prestation, 10)
        tarif_horaire = tarifs.get("tarif_horaire_standard", 0)
        estimation = heures * tarif_horaire

        calcul_details = [
            f"Heures estimées: {heures}",
            f"Tarif horaire standard: {tarif_horaire} €",
            f"Estimation initiale: {heures} x {tarif_horaire} = {estimation} €"
        ]

        if urgency == "Urgent":
            facteur_urgence = tarifs.get("facteur_urgence", 1.5)
            estimation *= facteur_urgence
            calcul_details.extend([
                f"Facteur d'urgence appliqué: x{facteur_urgence}",
                f"Estimation après urgence: {estimation} €"
            ])

        forfait = tarifs.get("forfaits", {}).get(prestation)
        if forfait:
            calcul_details.append(f"Forfait disponible: {forfait} €")
            if forfait < estimation:
                estimation = forfait
                calcul_details.append(f"Forfait appliqué: {forfait} €")

        estimation_basse, estimation_haute = round(estimation * 0.8), round(estimation * 1.2)
        calcul_details.append(f"Fourchette d'estimation: {estimation_basse} € - {estimation_haute} €")

        tarifs_utilises = {
            "tarif_horaire_standard": tarif_horaire,
            "facteur_urgence": tarifs.get("facteur_urgence") if urgency == "Urgent" else "Non appliqué",
            "forfait_prestation": forfait if forfait else "Pas de forfait"
        }

        return estimation_basse, estimation_haute, calcul_details, tarifs_utilises
    except Exception as e:
        logger.exception(f"Erreur dans calculate_estimate: {str(e)}")
        raise

def get_detailed_analysis(question: str, client_type: str, urgency: str, domaine: str, prestation: str) -> Tuple[str, Dict[str, Any], str]:
    prompt = f"""Analysez la question suivante et expliquez votre raisonnement pour le choix du domaine juridique et de la prestation.

Question : {question}
Type de client : {client_type}
Degré d'urgence : {urgency}
Domaine recommandé : {domaine}
Prestation recommandée : {prestation}

Structurez votre réponse en trois parties :
1. Analyse détaillée
2. Éléments spécifiques utilisés (JSON)
3. Sources d'information"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Vous êtes un assistant juridique expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )

        parts = response.choices[0].message.content.strip().split('\n\n', 2)
        analysis = parts[0] if parts else "Analyse non disponible."
        elements_used = json.loads(parts[1]) if len(parts) > 1 else {}
        sources = parts[2] if len(parts) > 2 else "Aucune source spécifique mentionnée."

        return analysis, elements_used, sources
    except Exception as e:
        logger.exception(f"Erreur lors de l'analyse détaillée : {e}")
        return "Une erreur s'est produite lors de l'analyse.", {"error": str(e)}, "Non disponible en raison d'une erreur."

def main():
    st.set_page_config(page_title="View Avocats - Devis en ligne", page_icon="⚖️", layout="wide")
    st.title("🏛️ View Avocats - Estimateur de devis")

    client_type = st.selectbox("Vous êtes :", ("Particulier", "Professionnel", "Société"))
    urgency = st.selectbox("Degré d'urgence :", ("Normal", "Urgent"))
    question = st.text_area("Expliquez brièvement votre cas :", height=150)

    if st.button("Obtenir une estimation"):
        if question:
            try:
                with st.spinner("Analyse en cours..."):
                    domaine, prestation = analyze_question(question, client_type, urgency)
                    estimation_basse, estimation_haute, calcul_details, tarifs_utilises = calculate_estimate(domaine, prestation, urgency)
                    detailed_analysis, elements_used, sources = get_detailed_analysis(question, client_type, urgency, domaine, prestation)

                st.success("Analyse terminée. Voici les résultats :")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Résumé de l'estimation")
                    st.write(f"**Domaine juridique :** {domaine}")
                    st.write(f"**Prestation :** {prestation}")
                    st.write(f"**Estimation :** Entre {estimation_basse} €HT et {estimation_haute} €HT")
                    
                    st.subheader("Détails du calcul")
                    for detail in calcul_details:
                        st.write(detail)

                with col2:
                    st.subheader("Éléments tarifaires utilisés")
                    st.json(tarifs_utilises)

                    if elements_used:
                        st.subheader("Éléments spécifiques pris en compte")
                        st.json(elements_used)

                st.subheader("Analyse détaillée")
                st.write(detailed_analysis)

                if sources:
                    st.subheader("Sources d'information")
                    st.write(sources)

                st.markdown("---")
                st.markdown("### 💡 Alternative Recommandée")
                st.info("**Consultation initiale d'une heure** - Tarif fixe : 100 € HT")

            except Exception as e:
                st.error(f"Une erreur s'est produite : {str(e)}")
        else:
            st.warning("Veuillez décrire votre cas avant de demander une estimation.")

    st.markdown("---")
    st.write("© 2024 View Avocats. Tous droits réservés.")

if __name__ == "__main__":
    main()
