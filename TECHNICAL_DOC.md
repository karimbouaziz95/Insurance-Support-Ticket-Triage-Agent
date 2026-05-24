# Technical Document: Insurance Support Ticket Triage Agent

---

## A. Problem Understanding

An insurance company receives a high volume of customer support tickets daily. Without automated triage, every ticket lands in a single queue and a human agent must manually read, classify, and route it to the right team. This is slow, error-prone, and requires the agent to have enough domain knowledge across billing, technical support, claims, and policy to correctly assess urgency and routing.

The goal of this agent is to automate first-pass triage — classify the topic, assess urgency, check whether the ticket has enough information to act on, and recommend the next action. The agent does not replace human agents, it ensures each ticket reaches the right person faster and urgent cases are not buried in the queue.

**Assumptions made:**

- Tickets are customer emails with a subject and a body
- Urgency is assessed from the text content only, no metadata like timestamps or customer history is used
- Ticket types map to 5 categories: Policy/Contract, Claims/Damage, Billing/Payment, Technical/Online Access, and Other
- Urgency has three levels: Low, Medium, and High — determined purely from the language and described severity in the ticket
- Routing follows a simplified team structure: billing team, technical support, claims team, and a supervisor escalation path
- High urgency tickets that are beyond a team's scope are escalated to a supervisor; all others are routed to the appropriate team
- A ticket is incomplete only when the problem itself is unclear, not just because a reference number is missing

---

## B. Data and Preprocessing

**Which part of the dataset was used:**

- Used `dataset-tickets-multi-lang-4-20k.csv` — the largest file with all relevant columns
- Filtered to English only (`language == "en"`) — the LLM performs best in English
- Used only `subject` and `body` fields — other fields such as `answer`, `tags`, `queue`, and `priority` were intentionally ignored to avoid leaking labels into the triage process
- Random sample of 200 tickets with a fixed seed (`random_state=42`) for reproducibility

**Preprocessing steps applied:**

- Dropped rows where `body` is null or empty — no content means nothing to triage
- Replaced null `subject` with empty string — subject is optional, body alone is sufficient to classify a ticket
- Used random sampling instead of `head()` — ensures a representative mix of ticket types rather than whatever happens to be at the top of the file
- No heavy NLP preprocessing was applied (no stemming, lemmatization, or stop word removal) — the LLM handles raw natural language well and these transformations can destroy signals useful for urgency or topic detection

---

## C. Architecture and Tools

**Overall Architecture**

The project is structured around three main components:

- `data/loader.py` — loads and preprocesses tickets from the dataset
- `agent/tools.py` — defines the 4 tool schemas exposed to the LLM
- `agent/orchestrator.py` — runs the agentic loop for each ticket
- `main.py` — entry point, loads tickets, calls the orchestrator, saves results to CSV

**Libraries and Models**

- `openai` (Python SDK) — used as the API client. The OpenAI-compatible interface allows swapping backends (Ollama, Groq, OpenAI) with a single line change, no other code changes needed
- `pandas` — dataset loading, filtering, and CSV output
- `python-dotenv` — manages API keys via `.env` file
- No orchestration framework such as LangChain was used intentionally — the agentic loop is implemented directly, making every step transparent and easy to explain and debug

The LLM backend is configurable — Ollama with `qwen3:4b` for local inference, Groq with `llama3-70b-8192` for free cloud inference, or OpenAI `gpt-4o-mini` for development.

**Agentic Orchestration**

The orchestrator runs a loop for each ticket:

1. The ticket subject and body are sent to the LLM along with 4 available tools
2. The LLM calls all 4 tools in order: `classify_topic`, `score_urgency`, `check_completeness`, `decide_next_action`
3. The tool call results are appended to the message history and sent back to the LLM
4. The LLM produces a final natural language summary
5. The tool call arguments are extracted from the message history and combined into a structured output dictionary

This gives a clear multi-step decision process as required, rather than a single unstructured model call.

---

## D. Agentic Workflow and Behavior

**Decision Logic**

For each ticket the agent follows a fixed sequence of steps enforced by the system prompt:

1. `classify_topic` — the LLM reads the subject and body and assigns one of 5 topic labels
2. `score_urgency` — the LLM assesses the severity and potential impact and assigns Low, Medium, or High
3. `check_completeness` — the LLM decides whether the problem is clear enough to act on. If not, it generates a specific clarification question to send back to the customer
4. `decide_next_action` — the LLM selects the most appropriate next action from 6 predefined options based on the topic, urgency, and completeness results

**Handling Missing or Unclear Tickets**

A ticket is considered incomplete only when the problem itself is unclear — not just because a reference number or policy number is missing. When the `check_completeness` tool flags a ticket as incomplete, the agent generates a targeted clarification question and sets the next action to "Request more information from customer".

**LLM vs Rules**

| Step | Method |
|---|---|
| Topic classification | LLM zero-shot |
| Urgency scoring | LLM zero-shot |
| Completeness check | LLM zero-shot |
| Next action decision | LLM zero-shot |

All 4 steps use LLM-based zero-shot reasoning — the model makes decisions based purely on its pre-trained knowledge and the system prompt instructions, with no labelled training data required. The tool schemas enforce structured output by constraining the LLM to predefined enum values, but the decision itself is always made by the model based on the ticket content.

---

## E. End-to-End Testing and Evaluation

**How the agent was tested**

The agent was tested manually during development by running individual tickets through the pipeline and inspecting the structured output. The following scenarios were covered:

| Scenario | Example | Expected behavior |
|---|---|---|
| Normal ticket | Incorrect invoice totals | Billing/Payment, Medium, Forward to billing team |
| High severity ticket | Medical data encryption failure exposing patient data | Technical/Online Access, High, Forward to tech or Escalate |
| Vague ticket | "Please help me" | Flagged as incomplete, clarification question generated |
| Out-of-scope ticket | Employee turnover implementation request | Other, FAQ or escalation |
| Billing with technical cause | Billing system glitch causing wrong invoice | Billing/Payment — the customer's problem is billing, not software |
| Data breach ticket | Apache Hadoop data breach | Technical/Online Access, High urgency |

The system prompt was iteratively refined based on observed errors. For example the completeness checker was initially too strict, flagging tickets as incomplete just because a policy number was missing. The prompt was updated to only flag tickets where the problem itself is unclear.

**Metrics to track in production**

- **Classification accuracy** — sample a batch of tickets weekly, have a human label them, and compare against the agent's predictions
- **Escalation rate** — if too high, urgency scoring is too aggressive; if too low, critical tickets may be missed
- **Incomplete ticket rate** — if too high, the completeness checker is too strict; if too low, agents are receiving tickets they cannot act on
- **Routing accuracy** — track how often a human agent re-routes a ticket after receiving it
- **LLM fallback rate** — frequency of missing or invalid tool call arguments, indicating model reliability issues
- **End-to-end latency** — time to process one ticket; alert if consistently above an acceptable threshold

---

## F. Limitations and Improvements

**Current Limitations**

*Data limitations:*
- The dataset contains IT support tickets, not insurance tickets. The topic labels are meaningful but the LLM has not seen insurance-specific vocabulary in context such as policy renewals, excess, or no-claims discount. This likely reduces classification accuracy on real insurance data.
- The dataset is heavily skewed toward Technical/Online Access tickets, meaning Claims/Damage and Policy/Contract are underrepresented in the output and harder to evaluate.

*Technical limitations:*
- Sequential processing — each ticket requires 2 LLM calls. Processing 200 tickets takes several minutes and is not suitable for real-time or high-volume production use.
- No memory between tickets — each ticket is processed independently. A returning customer with multiple open tickets gets no special treatment.
- Local model reliability — smaller open source models like `qwen3:4b` occasionally return malformed tool call arguments, requiring fallback defaults.
- Free tier rate limits — Groq's free tier has daily token limits that are easily hit when processing large batches.

*Quality limitations:*
- Urgency is assessed from text only — no metadata like submission time, customer history, or number of follow-ups is used.
- No feedback loop — if a human agent re-routes a ticket, that signal is lost and the agent cannot learn from corrections.
- The system prompt was tuned manually on a small sample and may not generalize well to all edge cases.

**If Given Two More Weeks**

- **Real insurance data** — validate and fine-tune the prompts on actual insurance tickets to improve topic classification accuracy
- **Async processing** — run LLM calls concurrently to reduce batch processing time significantly
- **Feedback loop** — build a simple interface where human agents can correct triage decisions, collecting labelled data over time
- **Confidence-based escalation** — if the model is uncertain about topic or urgency, automatically escalate rather than routing to a potentially wrong queue
- **Monitoring dashboard** — track classification distribution, escalation rate, incomplete rate, and latency over time
- **Deployment** — containerize with Docker and deploy on a cloud provider with a simple API endpoint so the agent can be called in real time as tickets arrive
