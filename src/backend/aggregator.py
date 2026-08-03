import json
import logging

# Set up basic logging so we can see errors in the terminal
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_agent_response(raw_response: str) -> str:
    """
    Takes the raw text/JSON output from Said's LangChain agents 
    and formats it cleanly for the Streamlit UI.
    """
    try:
        # First, try to parse it as a standard JSON dictionary
        # This handles cases where the agent outputs strict JSON
        parsed_data = json.loads(raw_response)
        
        # If it's a dictionary, let's format it beautifully into Markdown
        if isinstance(parsed_data, dict):
            formatted_output = "### Agent Task Report\n\n"
            for key, value in parsed_data.items():
                # Capitalize the key and make it bold
                clean_key = str(key).replace("_", " ").title()
                formatted_output += f"**{clean_key}:**\n{value}\n\n"
            return formatted_output
            
        # If it parsed but isn't a dict, just return it as a string
        return str(parsed_data)

    except json.JSONDecodeError:
        # If it fails to parse, it means the agent just sent normal conversational text.
        # In that case, we just return the text exactly as it is!
        logging.info("Response is not standard JSON, returning raw text.")
        return raw_response
        
    except Exception as e:
        # Catch-all for any weird formatting errors so it doesn't crash the dashboard
        logging.error(f"Error parsing agent output: {e}")
        return f"⚠️ **Output Parsing Error:** Could not format the agent's response. \n\n*Raw output:* {raw_response}"

# --- Quick Test (You can run this file directly to see it work) ---
if __name__ == "__main__":
    # Fake JSON from an agent
    fake_agent_output = '{"status": "success", "extracted_entities": ["User A", "Server B"], "confidence_score": "98%", "next_steps": "Awaiting manual approval."}'
    
    print("--- PARSED OUTPUT ---")
    print(parse_agent_response(fake_agent_output))