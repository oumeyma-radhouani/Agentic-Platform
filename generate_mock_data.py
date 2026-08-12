import json
import random

def generate_dataset(filename="synthetic_feedback.jsonl", num_records=50):
    feedback_templates = [
        ("The new interface is incredibly fast, but I couldn't find the export button.", 7, 8),
        ("Customer support was very rude on the phone yesterday.", 0, 6),
        ("The system crashed when I tried to upload a 50MB PDF.", 0, 6),
        ("I love the new features! Keep up the great work.", 9, 10),
        ("Billing charged me twice this month. I need a refund immediately.", 0, 6),
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(1, num_records + 1):
            feedback, minimum_score, maximum_score = random.choice(feedback_templates)
            nps = random.randint(minimum_score, maximum_score)
            
            record = {
                "feedback_id": f"TKT-{1000 + i}",
                "customer_id": f"CUST-{1000 + i}",
                "source": "Web",
                "score": nps,
                "comment": feedback,
                "language": "EN"
            }
            f.write(json.dumps(record) + '\n')
            
    print(f"Successfully generated {num_records} exact-schema records in {filename}")

if __name__ == "__main__":
    generate_dataset()
