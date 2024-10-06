import streamlit as st
import os
from openai import OpenAI
import json
import logging
from typing import Tuple, Dict, Any
import importlib.util

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY n'est pas défini dans les variables d'environnement")

client = OpenAI(api_key=OPENAI_API_KEY)

# Chargement des modules
def load_py_module(file_path: str, module_name: str):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        logger.error(f"Erreur lors du chargement du module {module_name}: {e}")
        return None

prestations_module = load_py_module('./prestations-heures.py', 'prestations_heures')
tarifs_module = load_py_module('./tarifs-prestations.py', 'tarifs_prestations')
instructions_module = load_py_module('./chatbot-instructions.py', 'consignes_chatbot')

prestations = prestations_module.get_prestations() if prestations_module else {}
tarifs = tarifs_module.get_tarifs() if tarifs_module else {}
instructions = instructions_module.get_chatbot_instructions() if instructions_module else ""

def get_openai_response(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API OpenAI: {e}")
        raise

def analyze_question(question: str, client_type: str, urgency: str) -> Tuple[str, str]:
    options = [f"{domaine}: {', '.join(prestations_domaine.keys())}" for domaine, prestations_domaine in prestations.items()]
    prompt = f"""Analysez la question suivante et identifiez le domaine juridique et la prestation la plus pertinente.

Question : {question}
Type de client : {client_type}
Degré d'urgence : {urgency}

Options de domaines et prestations :
{' '.join(options)}

Répondez avec le domaine et la prestation la plus pertinente, séparés par une virgule."""

    response = get_openai_response(prompt)
    return response.split(',', 1) if ',' in response else (response, "prestation générale")

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
2. Éléments spécifiques utilisés (format JSON valide)
3. Sources d'information

Assurez-vous que la partie 2 soit un JSON valide et strict."""

    try:
        response = get_openai_response(prompt)
        parts = response.split('\n\n', 2)
        
        analysis = parts[0] if parts else "Analyse non disponible."
        
        elements_used = {}
        if len(parts) > 1:
            try:
                json_lines = [line for line in parts[1].split('\n') if line.strip().startswith('{')]
                if json_lines:
                    elements_used = json.loads(''.join(json_lines))
                else:
                    logger.warning("Aucun JSON valide trouvé dans la réponse.")
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de décodage JSON : {e}")
                elements_used = {"error": "JSON invalide dans la réponse de l'API"}
        
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

                    st.subheader("Éléments spécifiques pris en compte")
                    if isinstance(elements_used, dict) and "error" not in elements_used:
                        st.json(elements_used)
                    else:
                        st.warning("Les éléments spécifiques n'ont pas pu être analysés correctement.")
                        if "error" in elements_used:
                            st.error(f"Erreur : {elements_used['error']}")

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
                logger.exception("Erreur dans le processus d'estimation")
        else:
            st.warning("Veuillez décrire votre cas avant de demander une estimation.")

    st.markdown("---")
    st.write("© 2024 View Avocats. Tous droits réservés.")

if __name__ == "__main__":
    main()
