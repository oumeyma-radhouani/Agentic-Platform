import json
import random
import uuid

# Aligned with the internship specifications for data sources
sources = [
    "Campagne d'Appels Satisfaction", 
    "Ticket Support SI",              
    "Historique Chat Client"          
]

segments = [
    {"name": "Enterprise", "arr_range": (100000, 500000)},
    {"name": "Mid-Market", "arr_range": (20000, 99999)},
    {"name": "SMB", "arr_range": (2000, 19999)}
]

account_managers = ["Sarah K.", "Marc D.", "Amine T.", "Julie L.", "Non Assigné"]

# Dynamic templates to ensure 50 unique comments
templates = {
    "positive": [
        "L'équipe technique a été très réactive. Le déploiement de notre {tech} s'est fait sans coupure. {detail}",
        "Excellent accompagnement de {manager} lors de la migration des bases de données. {detail}",
        "The transition to the new {tech} was seamless. {detail}",
        "Incident sur {tech} résolu rapidement. Le technicien a parfaitement compris notre architecture.",
    ],
    "negative": [
        "La migration a entraîné une perte temporaire de données de notre {tech}. {detail}",
        "We experienced an unexpected billing increase due to limits on {tech}. {detail}",
        "Plusieurs coupures critiques sur le service de {tech} cette semaine. {detail}",
        "The engineer assigned did not seem to understand our {tech} deployment. {detail}",
    ],
    "neutral": [
        "Service correct, mais l'intégration avec {tech} nécessite encore des ajustements. {detail}",
        "The initial setup for {tech} went well, but waiting for full operational status. {detail}",
        "L'installation s'est bien passée, on attend de voir la stabilité de {tech} sur le long terme.",
    ]
}

variables = {
    "tech": ["ERP", "Kubernetes cluster", "API gateway", "système de backup", "infrastructure cloud", "CRM", "Agent AI"],
    "detail": [
        "Temps d'attente inacceptable au support ce matin.",
        "L'expertise de CloudShift est indéniable.",
        "This was never communicated during the sales process.",
        "The automated insights reduced manual work by 40%.",
        "L'absence de communication proactive est décevante.",
        "Everything worked exactly as promised, preventing downtime.",
        "Documentation requires some trial and error."
    ],
    "manager": ["notre account manager", "l'équipe projet", "le support de niveau 2", "le service commercial"]
}

def generate_unique_comment(sentiment):
    template = random.choice(templates[sentiment])
    return template.format(
        tech=random.choice(variables["tech"]),
        detail=random.choice(variables["detail"]) if "{detail}" in template else "",
        manager=random.choice(variables["manager"])
    ).strip()

records = []
seen_comments = set()

for _ in range(50):
    # Weighted NPS distribution: 30% Detractors, 20% Passives, 50% Promoters
    score = random.choices(
        [random.randint(0, 6), random.randint(7, 8), random.randint(9, 10)], 
        weights=[0.3, 0.2, 0.5]
    )[0]
    
    sentiment = "negative" if score <= 6 else "neutral" if score <= 8 else "positive"
    
    # Ensure unique comment generation
    comment = generate_unique_comment(sentiment)
    while comment in seen_comments:
        comment = generate_unique_comment(sentiment)
    seen_comments.add(comment)

    # Assign operational metadata
    client_segment = random.choices(segments, weights=[0.2, 0.5, 0.3])[0]
    arr = random.randint(client_segment["arr_range"][0], client_segment["arr_range"][1])

    record = {
        "feedback_id": f"FBK-{uuid.uuid4().hex[:8].upper()}",
        "customer_id": f"CUST-{random.randint(1000, 9999)}",
        "source": random.choice(sources),
        "score": score,
        "comment": comment,
        "language": "FR" if "Le" in comment or "La" in comment or "L'" in comment or "Service" in comment else "EN",
        "operational_metadata": {
            "segment": client_segment["name"],
            "arr_euros": arr,
            "account_manager": random.choice(account_managers)
        }
    }
    
    records.append(record)

filename = "cloudshift_export_si_2026.json"
with open(filename, 'w', encoding='utf-8') as f:
    json.dump({"records": records}, f, indent=4, ensure_ascii=False)

print(f"Fichier '{filename}' généré avec succès ({len(records)} retours B2B qualifiés, 0 doublons).")