from openai import OpenAI
from dotenv import load_dotenv
import os
from data.loader import load_tickets
from agent.orchestrator import triage_ticket
import pandas as pd
import time

PATH_TO_DATA = "archive/dataset-tickets-multi-lang-4-20k.csv"

load_dotenv(override=True)

def main():


    # Initialize OpenAI client
    ## Ollama local
    client = OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')
    model_name = "qwen3:4b"

    ## Groq model
    #groq_api_key = os.getenv("GROQ_API_KEY")
    #client = OpenAI(
    #    api_key=groq_api_key, base_url="https://api.groq.com/openai/v1"
    #)
    #model_name = "openai/gpt-oss-120b"

    ## OpenAI model 
    #client = OpenAI()
    #model_name = "gpt-4o-mini"


    # Load and preprocess tickets
    tickets = load_tickets(PATH_TO_DATA, limit=500)

    # (Optional) Save the ticket IDs to a CSV file for reference
    df_ticket_ids = pd.DataFrame(tickets)
    df_ticket_ids.to_csv("triage_ticket_ids.csv", index=False)

    # Initialize list to store triage results
    triage_results = []

    # Triage each ticket and store the results
    for i, ticket in enumerate(tickets):
        print(f"Triaging ticket {ticket['id']} ({i+1}/{len(tickets)})...")
        triage_result = triage_ticket(ticket, client, model_name)
        triage_results.append(triage_result)
        time.sleep(1)  # Sleep for a short time to avoid hitting rate limits

    # Save triage results to a CSV file
    df = pd.DataFrame(triage_results)
    df.to_csv("triage_results.csv", index=False)


if __name__ == "__main__":
    main()