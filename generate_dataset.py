import json
import random
import uuid

# Aligned with the internship specifications for data sources
sources = [
    "Campagne d'Appels Satisfaction", # Rapports de satisfaction
    "Ticket Support SI",              # Données opérationnelles (Information System)
    "Historique Chat Client"          # Historiques d'interactions
]

# Highly realistic B2B/Tech feedback scenarios
feedbacks = {
    "positive": [
        {"comment": "L'équipe technique a été très réactive. Le déploiement de notre infrastructure cloud s'est fait sans coupure et dans le respect strict du SLA.", "language": "FR"},
        {"comment": "Excellent accompagnement de notre account manager lors de la migration des bases de données. L'expertise de CloudShift est indéniable.", "language": "FR"},
        {"comment": "The transition to the new agentic platform was seamless. The automated insights have already reduced our manual reporting time by 40%.", "language": "EN"},
        {"comment": "Incident de niveau 1 résolu en moins de 45 minutes. Le technicien a parfaitement compris notre architecture hybride.", "language": "FR"},
        {"comment": "Outstanding support during our peak traffic season. The auto-scaling features worked exactly as promised, preventing any downtime.", "language": "EN"}
    ],
    "negative": [
        {"comment": "La migration a entraîné une perte temporaire de données de notre ERP. Temps d'attente inacceptable au support téléphonique de niveau 2 ce matin.", "language": "FR"},
        {"comment": "We experienced a 15% increase in our monthly billing due to hidden API limits. This was never communicated during the sales process. Very disappointing.", "language": "EN"},
        {"comment": "Plusieurs coupures critiques sur le service de backup cette semaine. L'absence de communication proactive de la part de l'équipe SI est inacceptable.", "language": "FR"},
        {"comment": "The support engineer assigned to our ticket did not seem to understand our Kubernetes deployment. We had to explain our infrastructure three times.", "language": "EN"},
        {"comment": "Impossible de joindre le service commercial pour réajuster nos licences. Le portail en ligne renvoie systématiquement une erreur 500 depuis mardi.", "language": "FR"}
    ],
    "neutral": [
        {"comment": "Service correct dans l'ensemble, mais les tarifs de la nouvelle grille restent élevés par rapport aux concurrents du marché.", "language": "FR"},
        {"comment": "The initial setup went well, but we are still waiting for the custom dashboard features to be fully operational.", "language": "EN"},
        {"comment": "L'installation s'est bien passée, on attend de voir la stabilité du réseau sur le long terme avant de déployer sur nos autres sites.", "language": "FR"},
        {"comment": "Average experience. The documentation for the new API endpoints is somewhat lacking and requires trial and error.", "language": "EN"}
    ]
}

records = []

# Generate 50 professional, schema-compliant feedback records
for _ in range(50):
    # Weighted NPS distribution: 30% Detractors, 20% Passives, 50% Promoters
    score = random.choices(
        [random.randint(0, 6), random.randint(7, 8), random.randint(9, 10)], 
        weights=[0.3, 0.2, 0.5]
    )[0]
    
    # Assign category based on NPS score logic
    if score <= 6:
        selection = random.choice(feedbacks["negative"])
    elif score <= 8:
        selection = random.choice(feedbacks["neutral"])
    else:
        selection = random.choice(feedbacks["positive"])

    # Build the record exactly as the backend Pydantic schema expects
    record = {
        "feedback_id": f"FBK-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "source": random.choice(sources),
        "score": score,
        "comment": selection["comment"],
        "language": selection["language"]
    }
    
    records.append(record)

# Wrap in the expected {"records": [...]} format and save
filename = "cloudshift_export_si_2026.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump({"records": records}, f, indent=4, ensure_ascii=False)

print(f"Fichier '{filename}' généré avec succès ({len(records)} retours B2B qualifiés).")