import streamlit as st
import os
from openai import OpenAI
import json
import logging
from typing import Tuple, Dict, Any
import importlib.util

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration du client OpenAI
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

# Initialisation des variables globales
prestations = prestations_module.get_prestations() if prestations_module else {}
tarifs = tarifs_module.get_tarifs() if tarifs_module else {}
instructions = instructions_module.get_chatbot_instructions() if instructions_module else ""

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

def check_response_relevance(response: str, options: list) -> bool:
    response_lower = response.lower()
    return any(option.lower().split(':')[0].strip() in response_lower for option in options)

def analyze_question(question: str, client_type: str, urgency: str) -> Tuple[str, str, float, bool]:
    options = [f"{domaine}: {', '.join(prestations_domaine.keys())}" for domaine, prestations_domaine in prestations.items()]
    prompt = f"""Analysez la question suivante et identifiez le domaine juridique et la prestation la plus pertinente.

Question : {question}
Type de client : {client_type}
Degré d'urgence : {urgency}

Options de domaines et prestations :
{' '.join(options)}

Répondez avec le domaine et la prestation la plus pertinente, séparés par une virgule."""

    response, confidence = get_openai_response(prompt)
    
    is_relevant = check_response_relevance(response, options)
    
    if is_relevant:
        domain, service = response.split(',', 1) if ',' in response else (response, "prestation générale")
        return domain.strip(), service.strip(), confidence, True
    else:
        return "", "", confidence, False

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
    prompt = f"""En tant qu'assistant juridique virtuel pour View Avocats, analysez la question suivante et expliquez votre raisonnement pour le choix du domaine juridique et de la prestation.

Question : {question}
Type de client : {client_type}
Degré d'urgence : {urgency}
Domaine recommandé : {domaine}
Prestation recommandée : {prestation}

Structurez votre réponse en trois parties clairement séparées par des lignes vides :

1. Analyse détaillée :
Fournissez une analyse concise mais détaillée du cas, en tenant compte du type de client et du degré d'urgence.

2. Éléments spécifiques utilisés (format JSON strict) :
{{"domaine": {{"nom": "nom_du_domaine", "description": "description_du_domaine"}}, "prestation": {{"nom": "nom_de_la_prestation", "description": "description_de_la_prestation"}}}}

3. Sources d'information :
Listez les sources d'information utilisées pour cette analyse, si applicable.

Assurez-vous que chaque partie est clairement séparée et que le JSON dans la partie 2 est valide et strict."""

    try:
        response, _ = get_openai_response(prompt)
        logger.info(f"Réponse brute de l'API : {response}")

        parts = response.split('\n\n')
        
        analysis = parts[0] if len(parts) > 0 else "Analyse non disponible."
        
        elements_used = {}
        if len(parts) > 1:
            try:
                json_part = next((part for part in parts if '{' in part and '}' in part), None)
                if json_part:
                    json_str = json_part[json_part.index('{'):json_part.rindex('}')+1]
                    elements_used = json.loads(json_str)
                else:
                    logger.warning("Aucun JSON valide trouvé dans la réponse.")
                    elements_used = {
                        "domaine": {"nom": domaine, "description": "Information non fournie par l'API"},
                        "prestation": {"nom": prestation, "description": "Information non fournie par l'API"}
                    }
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de décodage JSON : {e}")
                elements_used = {
                    "domaine": {"nom": domaine, "description": "Erreur dans l'analyse de la réponse"},
                    "prestation": {"nom": prestation, "description": "Erreur dans l'analyse de la réponse"}
                }
        else:
            elements_used = {
                "domaine": {"nom": domaine, "description": "Information non disponible"},
                "prestation": {"nom": prestation, "description": "Information non disponible"}
            }
        
        sources = parts[2] if len(parts) > 2 else "Aucune source spécifique mentionnée."

        return analysis, elements_used, sources
    except Exception as e:
        logger.exception(f"Erreur lors de l'analyse détaillée : {e}")
        return "Une erreur s'est produite lors de l'analyse.", {
            "domaine": {"nom": domaine, "description": "Erreur dans l'analyse"},
            "prestation": {"nom": prestation, "description": "Erreur dans l'analyse"}
        }, "Non disponible en raison d'une erreur."

def main():
    st.set_page_config(page_title="View Avocats - Devis IA en ligne", page_icon="⚖️", layout="wide")
    st.title("🏛️ View Avocats - Estimateur de Devis Propulsé par l'IA")
    
    st.markdown("""
    ### Découvrez la puissance de l'IA juridique !
    Notre estimateur de devis utilise une intelligence artificielle de pointe pour analyser votre situation 
    et vous fournir une estimation personnalisée en quelques secondes.
    """)

    client_type = st.selectbox("Vous êtes :", ("Particulier", "Professionnel", "Société"))
    urgency = st.selectbox("Degré d'urgence :", ("Normal", "Urgent"))
    question = st.text_area("Décrivez votre cas juridique et laissez notre IA faire le reste :", height=150,
                            help="Plus vous fournissez de détails, plus notre IA sera précise dans son analyse.")

    if st.button("Lancer l'analyse IA"):
        if question:
            try:
                with st.spinner("🤖 Notre IA juridique analyse votre cas..."):
                    domaine, prestation, confidence, is_relevant = analyze_question(question, client_type, urgency)

                if is_relevant:
                    estimation_basse, estimation_haute, calcul_details, tarifs_utilises = calculate_estimate(domaine, prestation, urgency)
                    detailed_analysis, elements_used, sources = get_detailed_analysis(question, client_type, urgency, domaine, prestation)

                    st.success("🎉 Analyse IA terminée avec succès ! Voici vos résultats personnalisés :")
                    
                    st.subheader("🧠 Indice de confiance de l'IA")
                    st.progress(confidence)
                    st.write(f"Confiance de l'IA : {confidence:.2%}")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("💡 Résumé de l'estimation IA")
                        st.write(f"**Domaine juridique identifié :** {domaine}")
                        st.write(f"**Prestation recommandée par l'IA :** {prestation}")
                        st.write(f"**Estimation IA :** Entre {estimation_basse} €HT et {estimation_haute} €HT")
                        
                        st.subheader("🔍 Détails du calcul IA")
                        for detail in calcul_details:
                            st.write(detail)

                    with col2:
                        st.subheader("💼 Éléments tarifaires analysés par l'IA")
                        st.json(tarifs_utilises)

                        st.subheader("🧩 Éléments spécifiques identifiés par l'IA")
                        if isinstance(elements_used, dict) and "domaine" in elements_used and "prestation" in elements_used:
                            st.json(elements_used)
                        else:
                            st.warning("Notre IA n'a pas pu analyser tous les éléments de manière optimale.")
                            st.json(elements_used)

                    st.subheader("📊 Analyse détaillée de l'IA")
                    st.write(detailed_analysis)

                    if sources and sources != "Aucune source spécifique mentionnée.":
                        st.subheader("📚 Sources d'information utilisées par l'IA")
                        st.write(sources)

                    st.markdown("---")
                    st.markdown("### 💡 Recommandation IA")
                    st.info("**Consultation initiale d'une heure avec un avocat expert** - Tarif fixe : 100 € HT")

                else:
                    st.warning("🤔 Notre IA a rencontré des difficultés pour analyser précisément votre cas juridique.")
                    st.info("👨‍⚖️ Pour une assistance personnalisée, nous vous recommandons de contacter directement le cabinet View Avocats par email ou par téléphone au [insérez le numéro ici]. Nos experts humains seront ravis de vous aider !")

            except Exception as e:
                st.error(f"Une erreur inattendue s'est produite dans notre système IA : {str(e)}")
                logger.exception("Erreur dans le processus d'estimation IA")
        else:
            st.warning("⚠️ Veuillez décrire votre cas pour que notre IA puisse l'analyser.")

    st.markdown("---")
    st.markdown("""
    ### Pourquoi choisir notre estimateur IA ?
    - **Rapide** : Obtenez une estimation en quelques secondes
    - **Précis** : Notre IA est entraînée sur des milliers de cas juridiques
    - **Disponible 24/7** : Accédez à une expertise juridique à tout moment
    - **Innovant** : Bénéficiez des dernières avancées en IA juridique
    """)
    st.write("© 2024 View Avocats. Tous droits réservés. Propulsé par l'IA de pointe.")

if __name__ == "__main__":
    main()
