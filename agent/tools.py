
# Define the tools that the model can use to triage the support tickets
classify_topic_tool = {
    "type": "function",
    "function": {
        "name": "classify_topic",
        "description": "Classify the topic of a support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "enum": [
                        "Policy / Contract",
                        "Claims / Damage",
                        "Billing / Payment",
                        "Technical / Online Access",
                        "Other"
                    ],
                    "description": "The topic of the support ticket"
                }
            },
            "required": ["topic"]
        }
    }
}

score_urgency_tool = {
    "type": "function",
    "function": {
        "name": "score_urgency",
        "description": "Score the urgency of a support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "urgency": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High"],
                    "description": "The urgency score of the support ticket"
                }
            },
            "required": ["urgency"]
        }
    }
}

check_completeness_tool = {
    "type": "function",
    "function": {
        "name": "check_completeness",
        "description": "Check the completeness of a support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "is_complete": {
                    "type": "boolean",
                    "description": "Whether the support ticket is complete or not"
                },
                "clarification_question": {
                    "type": "string",
                    "description": "The clarification question to ask if the support ticket is incomplete"
                }
            },
            "required": ["is_complete"]
        }
    }
}

decide_next_action_tool = {
    "type": "function",
    "function": {
        "name": "decide_next_action",
        "description": "Decide the next action to take for a support ticket",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "Send standard FAQ or self-service link",
                        "Create or update a claim",
                        "Forward to billing team",
                        "Forward to technical support team",
                        "Escalate to human supervisor",
                        "Request more information from customer"
                    ],
                    "description": "The next action to take for the support ticket"
                }
            },
            "required": ["action"]
        }
    }
}

tools = [
    classify_topic_tool,
    score_urgency_tool,
    check_completeness_tool,
    decide_next_action_tool
]