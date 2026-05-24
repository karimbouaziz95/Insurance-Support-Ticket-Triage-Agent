from openai import OpenAI

import json

from agent.tools import tools


system_prompt = """
You are an Insurance Support Ticket Triage Agent that helps an insurance 
company route and prioritize incoming customer tickets.
You should read and analyze the subject and body of the ticket carefully, 
then call the appropriate tools to classify the topic, score the urgency, 
check the completeness, and decide the next action for every ticket 
you receive.

For every ticket you receive, you must always call all 4 tools in this order:
1. classify_topic
2. score_urgency
3. check_completeness
4. decide_next_action

Analyze the subject and body of the ticket carefully before calling each tool.

A ticket is incomplete only when the problem itself is unclear, 
not just because some reference number is missing.

The topic Technical / Online Access is for tickets related to technical 
issues, such as, software, security incidents, data breaches, 
system access issues, and other IT-related problems.

The topic Policy / Contract is for tickets related to questions about the 
insurance policy, contract details, coverage, terms and conditions, 
policy changes, and other related inquiries.

The topic Claims / Damage is for tickets related to claims, damages, accidents,
and other related issues.

The topic Billing / Payment is for tickets related to billing, payments, 
invoices, refunds, and other related issues.

The topic Other is for tickets that do not fit into any of the other topics.

High urgency tickets should be escalated to a human supervisor only when
they are beyond what a team can handle, otherwise forwarded them to the 
appropriate team.

Use your judgment to assess urgency based on the severity and potential 
impact of the issue described in the ticket.

"""

def output_result(ticket: dict, messages: list) -> dict:
    """
    Extract the triage result from the messages and return it as a dictionary.
    The dictionary should have the following format:
    {
        "ticket_id": str,
        "text_snippet": str,
        "topic": str,
        "urgency": str,
        "next_action": str,
        "is_complete": bool,
        "clarification_question": str or None,
        "notes": str
    }
    """

    
    result = {
    "ticket_id": ticket["id"],
    "text_snippet": (ticket["subject"] + ": " + ticket["body"])[:150],
    "topic": None,
    "urgency": None,
    "next_action": None,
    "is_complete": None,
    "clarification_question": None,
    "notes": ""
    }

    for message in messages:

        if hasattr(message, "tool_calls") and message.tool_calls:

            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)

                if tool_call.function.name == "classify_topic":
                    result["topic"] = args.get("topic", "Other")

                elif tool_call.function.name == "score_urgency":
                    result["urgency"] = args.get("urgency", "Medium")

                elif tool_call.function.name == "check_completeness":
                    result["is_complete"] = args.get("is_complete", True)
                    result["clarification_question"] = args.get(
                        "clarification_question", None
                    )

                elif tool_call.function.name == "decide_next_action":
                    result["next_action"] = args.get(
                        "action", "Escalate to human supervisor"
                    )

    return result


def triage_ticket(ticket: dict, client: OpenAI, model_name: str) -> dict:
    """
    Triage a support ticket and assign it to the appropriate team.
    """
    
    # Create the content of the ticket to be analyzed by the model
    content_of_the_ticket = f"""
    Here is a ticket that needs to be triaged:
    Subject: {ticket['subject']}
    Body: {ticket['body']}
    """

    # Initialize the messages with the system prompt and the content of the ticket
    messages = \
        [{"role": "system", "content": system_prompt}] + \
        [{"role": "user", "content": content_of_the_ticket}]

    done = False

    # Loop until the model finishes without calling any tools
    while not done:

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools
        )

        finish_reason = response.choices[0].finish_reason

        if finish_reason == "tool_calls":
            # Handle tool calls here
            messages.append(response.choices[0].message)

            for tool_call in response.choices[0].message.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "ok"
                })
        else:
            done = True
    
    # Extract the triage result from the messages and return it as a dictionary
    ticket_triage_result = output_result(ticket, messages)
    notes = response.choices[0].message.content.split("\n\n")[-1].strip()
    ticket_triage_result["notes"] = notes

    return ticket_triage_result