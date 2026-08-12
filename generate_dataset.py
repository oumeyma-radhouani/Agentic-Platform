import json
import random
import uuid

sources = ["Campagne Appel Q3", "Support Ticket", "Appel de Rétention"]

# Base de commentaires réalistes
commentaires_positifs = [
    "L'équipe technique a été très réactive. Le déploiement s'est fait sans coupure.",
    "Excellent accompagnement de notre account manager lors de la migration.",
    "La nouvelle interface du dashboard est beaucoup plus intuitive.",
    "Problème résolu en moins de 2h, service impeccable comme toujours.",
    "Très satisfait des performances des nouveaux serveurs cloud."
]

commentaires_negatifs = [
    "Temps d'attente interminable au support téléphonique ce matin.",
    "La facture a augmenté de 15% sans aucune explication préalable. Inadmissible.",
    "Plusieurs coupures sur le service de backup cette semaine. C'est critique pour nous.",
    "Le technicien ne semblait pas maîtriser notre environnement hybride.",
    "Impossible de joindre le service commercial pour ajouter des licences."
]

commentaires_neutres = [
    "Service correct, mais les tarifs restent élevés.",
    "L'installation s'est bien passée, on attend de voir sur le long terme.",
    "Rien à signaler pour le moment, ça fonctionne."
]

records = []

# Générer 50 faux retours clients ultra-réalistes
for i in range(50):
    # Génération d'une note aléatoire (avec une tendance pour avoir un peu de tout)
    score = random.choices([random.randint(0, 6), random.randint(7, 8), random.randint(9, 10)], weights=[0.3, 0.2, 0.5])[0]
    
    # Choix du commentaire en fonction de la note
    if score <= 6:
        comment = random.choice(commentaires_negatifs)
    elif score <= 8:
        comment = random.choice(commentaires_neutres)
    else:
        comment = random.choice(commentaires_positifs)

    # Schéma canonique feedback v1
    record = {
        "feedback_id": f"FB-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "source": random.choice(sources),
        "score": score,
        "comment": comment,
        "language": "FR"
    }
    
    records.append(record)

# Sauvegarder dans un fichier JSON prêt pour l'upload
filename = "cloudshift_export_si_2026.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump({"records": records}, f, indent=4, ensure_ascii=False)

print(f"Fichier '{filename}' genere avec succes ({len(records)} retours au schema v1).")
