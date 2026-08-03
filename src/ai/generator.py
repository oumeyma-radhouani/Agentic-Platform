import os
import json
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# 1. Setup Azure OpenAI Credentials (Securely)
# This automatically loads all your keys from the hidden .env file
load_dotenv()

# 2. Define the Strict Data Contract
# This ensures GPT-5.mini outputs the exact JSON structure Saïd's backend expects
class FeedbackRecord(BaseModel):
    feedback_id: str = Field(description="Unique ID, e.g., FBK-001")
    customer_id: str = Field(description="Customer ID, e.g., CUST-890")
    source: str = Field(description="Controlled value: Web, App, or Email")
    score: int = Field(description="NPS score strictly from 0 to 10")
    comment: str = Field(description="The customer feedback text")
    language: str = Field(description="Language of the comment: EN or FR")

class FeedbackBatch(BaseModel):
    records: List[FeedbackRecord]

# 3. Initialize the Azure Model
llm = AzureChatOpenAI(
    deployment_name=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    api_version=os.environ["AZURE_OPENAI_API_VERSION"], 
    temperature=0.8, 
)

parser = JsonOutputParser(pydantic_object=FeedbackBatch)

# 4. The Prompt Instructions
prompt = PromptTemplate(
    template="""You are a data generation assistant for a customer service platform.
Your task is to generate realistic customer feedback records.
    
REQUIREMENTS:
- Generate exactly {count} records.
- Include a mix of positive, neutral, negative, and mixed feedback.
- Include edge cases: sarcastic comments, multi-topic complaints, and vague complaints.
- Write the 'comment' field in French (50%) and English (50%).
- Scores must be strictly integers between 0 and 10.

{format_instructions}
""",
    input_variables=["count"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)

chain = prompt | llm | parser

def generate_golden_dataset(total_records=200, batch_size=20):
    all_records = []
    
    print(f"🚀 Starting generation of {total_records} records via Azure GPT-5.mini...")
    
    # Loop to generate in safe batches
    for i in range(0, total_records, batch_size):
        print(f"Generating batch {(i // batch_size) + 1}...")
        try:
            result = chain.invoke({"count": batch_size})
            all_records.extend(result["records"])
        except Exception as e:
            print(f"Error generating batch: {e}")
            
    # Save the final compiled array to the shared data folder
    # Calcule le chemin absolu vers le dossier racine du projet
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "..", "..", "data", "golden_dataset.json")
    
    # Crée le dossier s'il n'existe pas
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Sauvegarde le fichier
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Success! {len(all_records)} records saved to {output_path}")

if __name__ == "__main__":
    generate_golden_dataset(total_records=200, batch_size=20)