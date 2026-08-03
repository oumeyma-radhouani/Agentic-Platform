import json
import random

def generate_dataset(filename="synthetic_feedback.jsonl", num_records=50):
    feedback_templates = [
        ("The new interface is incredibly fast, but I couldn't find the export button.", "UI/UX"),
        ("Customer support was very rude on the phone yesterday.", "Customer Service"),
        ("The system crashed when I tried to upload a 50MB PDF.", "Technical Issue"),
        ("I love the new features! Keep up the great work.", "Positive Feedback"),
        ("Billing charged me twice this month. I need a refund immediately.", "Billing")
    ]
    
    with open(filename, 'w', encoding='utf-8') as f:
        for i in range(1, num_records + 1):
            feedback, category = random.choice(feedback_templates)
            nps = random.randint(0, 10)
            
            record = {
                "feedback_id": f"TKT-{1000 + i}",
                "comment": feedback,
                "score": nps,
                "metadata": {"source": "web_portal", "category_hint": category}
            }
            f.write(json.dumps(record) + '\n')
            
    print(f"Successfully generated {num_records} exact-schema records in {filename}")

if __name__ == "__main__":
    generate_dataset()