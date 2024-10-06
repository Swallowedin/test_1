import streamlit as st
import os
from openai import OpenAI
import json
import logging
from typing import Tuple, Dict, Any
import importlib.util
from statistics import mean, stdev

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration du client OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY n'est pas défini dans les variables d'environnement")

client = OpenAI(api_key=OPENAI_API_KEY)

# ... [Le reste du code reste inchangé jusqu'à la fonction get_openai_response]

def get_openai_response(prompt: str, model: str = "gpt-3.5-turbo", num_iterations: int = 5) -> Tuple[str, float]:
    try:
        responses = []
        for _ in range(num_iterations):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            content = response.choices[0].message.content.strip()
            responses.append(content)
        
        # Calculer la réponse la plus fréquente et l'indice de confiance
        most_common = max(set(responses), key=responses.count)
        confidence = responses.count(most_common) / num_iterations
        
        logger.info(f"Réponse la plus fréquente : {most_common}")
        logger.info(f"Indice de confiance : {confidence}")
        
        return most_common, confidence
    except Exception as e:
        logger.error(f"Erreur lors de l'appel à l'API OpenAI: {e}")
        raise

def analyze_question(question: str, client_type: str, urgency: str) -> Tuple[str, str, float]:
    options = [f"{domaine}: {', '.join(prestations_domaine.keys())}" for domaine, prestations_domaine in prestations.items()]
    prompt = f"""Analysez la question suivante et identifiez le domaine juridique et la prestation la plus pertinente.

Question : {question}
Type de client : {client_type}
Degré d'urgence : {urgency}

Options de domaines et prestations :
{' '.join(options)}

Répondez avec le domaine et la prestation la plus pertinente, séparés par une virgule."""

    response, confidence = get_openai_response(prompt)
    domain, service = response.split(',', 1) if ',' in response else (response, "prestation générale")
    return domain.strip(), service.strip(), confidence

# ... [Le reste des fonctions reste inchangé]

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
                    domaine, prestation, confidence = analyze_question(question, client_type, urgency)
                    estimation_basse, estimation_haute, calcul_details, tarifs_utilises = calculate_estimate(domaine, prestation, urgency)
                    detailed_analysis, elements_used, sources = get_detailed_analysis(question, client_type, urgency, domaine, prestation)

                st.success("Analyse terminée. Voici les résultats :")
                
                # Affichage de la barre de confiance
                st.subheader("Indice de confiance de l'analyse")
                st.progress(confidence)
                st.write(f"Confiance : {confidence:.2%}")

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

                if sources and sources != "Aucune source spécifique mentionnée.":
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
