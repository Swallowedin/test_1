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
    # ... [Le reste de la fonction main reste inchangé]

if __name__ == "__main__":
    main()
