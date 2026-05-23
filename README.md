# Insurance Support Ticket Triage Agent

This project is a small Python prototype for triaging customer support tickets in an insurance context. It loads tickets from the public Kaggle multilingual customer support ticket dataset, treats the tickets as insurance support requests, and uses an LLM-based multi-step workflow to classify, prioritize, and route each ticket.

The current implementation runs as a CLI batch processor. It reads a sample of tickets, sends each ticket through the triage workflow, and writes structured triage results to a CSV file.

## What The Agent Does

For each ticket, the agent produces:

- Ticket ID
- Original ticket text
- Predicted topic
- Predicted urgency
- Suggested next action
- Completeness flag
- Optional clarification question
- Optional notes

The triage workflow is intentionally split into multiple internal steps:

1. Classify the ticket topic.
2. Score ticket urgency.
3. Check whether the ticket contains enough information.
4. Decide the next action.
5. Save the combined result as structured output.

This gives the prototype a clear agentic decision process instead of a single unstructured model response.

## Project Structure

```text
.
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py      # LLM orchestration and triage workflow
│   └── tools.py             # Tool/function schemas used by the model
├── archive/
│   └── dataset-tickets-multi-lang-4-20k.csv
├── data/
│   └── loader.py            # Dataset loading and preprocessing
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── triage_results.csv       # Example generated output
└── README.md
```

## Requirements

- Python 3.10 or newer
- A Groq API key
- The Kaggle customer support ticket dataset

The prototype uses Groq through an OpenAI-compatible API client. The configured model is:

```python
openai/gpt-oss-120b
```

This satisfies the assignment requirement to use an LLM-based component with a free-tier/open model backend. The orchestration code uses the OpenAI-compatible client interface, so the backend can be changed later to another compatible provider or local endpoint if needed.

## Step 1: Clone Or Open The Project

If you already have the project folder locally, open a terminal in the project root:

```bash
cd /path/to/AssignmentHDI
```

For example:

```bash
cd ~/Desktop/AssignmentHDI
```

## Step 2: Create A Virtual Environment

Create a Python virtual environment:

```bash
python3 -m venv .venv
```

Activate it on macOS or Linux:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, your shell prompt should show that `.venv` is active.

## Step 3: Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

The main dependencies are:

- `openai`: OpenAI-compatible API client used to call Groq.
- `python-dotenv`: Loads environment variables from `.env`.
- `pandas`: Reads the dataset and writes CSV output.
- `groq`: Included for Groq compatibility, although the current code uses Groq through the OpenAI-compatible endpoint.

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add your Groq API key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

You can create or find your Groq API key in the Groq console.

Important:

- Do not commit your real `.env` file to a public repository.
- The code reads this value in `main.py` using `python-dotenv`.
- If the key is missing or invalid, the script will fail when it tries to call the model.

## Step 5: Download The Dataset From Kaggle

The assignment asks to use this dataset:

```text
Customer IT Support - Ticket Dataset
https://www.kaggle.com/datasets/tobiasbueck/multilingual-customer-support-tickets
```

You can download it in either of the following ways.

### Option A: Download From The Kaggle Website

1. Open the dataset page:

   ```text
   https://www.kaggle.com/datasets/tobiasbueck/multilingual-customer-support-tickets
   ```

2. Sign in to Kaggle.
3. Click **Download**.
4. Extract the downloaded ZIP file.
5. Copy the dataset files into the project `archive/` folder.

The code currently expects this file:

```text
archive/dataset-tickets-multi-lang-4-20k.csv
```

If your downloaded file has a different name, either rename the file or update `PATH_TO_DATA` in `main.py`.

### Option B: Download With The Kaggle CLI

Install the Kaggle CLI if needed:

```bash
pip install kaggle
```

Configure your Kaggle API token:

1. Go to your Kaggle account settings.
2. Create an API token.
3. Place the downloaded `kaggle.json` file in:

   ```text
   ~/.kaggle/kaggle.json
   ```

4. Make sure the file permissions are restricted:

   ```bash
   chmod 600 ~/.kaggle/kaggle.json
   ```

Download the dataset:

```bash
kaggle datasets download -d tobiasbueck/multilingual-customer-support-tickets
```

Create the archive folder if it does not exist:

```bash
mkdir -p archive
```

Unzip the dataset into `archive/`:

```bash
unzip multilingual-customer-support-tickets.zip -d archive
```

Check that the expected CSV exists:

```bash
ls archive/
```

If the file name differs, update this line in `main.py`:

```python
PATH_TO_DATA = "archive/dataset-tickets-multi-lang-4-20k.csv"
```

## Step 6: Run The Triage Agent

Run the batch processor:

```bash
python main.py
```

By default, the script:

1. Loads the CSV from `archive/dataset-tickets-multi-lang-4-20k.csv`.
2. Filters the dataset to English tickets.
3. Drops tickets with missing or empty body text.
4. Samples 200 tickets with a fixed random seed.
5. Runs each ticket through the LLM triage workflow.
6. Writes the results to a CSV file.

The current output file is:

```text
triage_results_groq.csv
```

Depending on rate limits and model latency, processing 200 tickets can take several minutes. The script includes a short delay between requests to reduce the chance of hitting rate limits.

## Running A Smaller Sample Batch

For quick testing, reduce the sample size in `main.py`:

```python
tickets = load_tickets(PATH_TO_DATA, limit=10)
```

Then run:

```bash
python main.py
```

This is useful when validating API credentials or checking formatting before running the full 200-ticket batch.

Before final submission, set the limit back to at least 200:

```python
tickets = load_tickets(PATH_TO_DATA, limit=200)
```

## Output Format

The generated CSV contains one row per processed ticket.

Expected columns:

```text
ticket_id
content
topic
urgency
next_action
is_complete
clarification_question
notes
```

Example row:

```text
ticket_id: 12224
topic: Technical / Online Access
urgency: High
next_action: Forward to technical support team
is_complete: True
notes: The ticket will be forwarded to the technical support team for immediate assistance.
```

The supported topic labels are:

- `Policy / Contract`
- `Claims / Damage`
- `Billing / Payment`
- `Technical / Online Access`
- `Other`

The supported urgency labels are:

- `Low`
- `Medium`
- `High`

The supported next actions are:

- `Send standard FAQ or self-service link`
- `Create or update a claim`
- `Forward to billing team`
- `Forward to technical support team`
- `Escalate to human supervisor`
- `Request more information from customer`

## How The Workflow Works

The entry point is `main.py`.

`main.py` performs the batch-level work:

1. Loads environment variables.
2. Creates the Groq/OpenAI-compatible client.
3. Loads a ticket subset from the dataset.
4. Calls `triage_ticket()` for each ticket.
5. Saves all results to CSV.

`data/loader.py` handles dataset loading:

1. Reads the CSV with pandas.
2. Keeps English tickets.
3. Removes empty ticket bodies.
4. Samples a reproducible subset.
5. Returns ticket dictionaries with `id`, `subject`, and `body`.

`agent/orchestrator.py` handles the agent workflow:

1. Builds the system prompt.
2. Sends the ticket to the LLM.
3. Requires the model to call the four triage tools.
4. Extracts the tool-call arguments.
5. Builds a final result dictionary.

`agent/tools.py` defines the model tool schemas:

1. `classify_topic`
2. `score_urgency`
3. `check_completeness`
4. `decide_next_action`

## Configuration

The main configuration values are in `main.py`.

Dataset path:

```python
PATH_TO_DATA = "archive/dataset-tickets-multi-lang-4-20k.csv"
```

Model backend:

```python
client = OpenAI(
    api_key=groq_api_key,
    base_url="https://api.groq.com/openai/v1"
)
```

Model name:

```python
model_name = "openai/gpt-oss-120b"
```

Batch size:

```python
tickets = load_tickets(PATH_TO_DATA, limit=200)
```

Output file:

```python
df.to_csv("triage_results_groq.csv", index=False)
```

## Troubleshooting

### Missing API Key

If you see an authentication error, check that `.env` exists and contains:

```env
GROQ_API_KEY=your_groq_api_key_here
```

Also make sure `load_dotenv(override=True)` is still called in `main.py`.

### Dataset File Not Found

If you see a file-not-found error, check that the CSV exists at:

```text
archive/dataset-tickets-multi-lang-4-20k.csv
```

If the file has a different name, update `PATH_TO_DATA` in `main.py`.

### Rate Limit Errors

The script currently waits between tickets:

```python
time.sleep(1)
```

If you hit rate limits, increase this delay or run a smaller batch while testing.

### Slow Runtime

Processing 200 tickets requires 200 model calls, and some tickets may require multiple tool-call turns. To test quickly, use a smaller batch size such as 5 or 10.

### Empty Or Missing Output Fields

The output fields are extracted from model tool calls. If a field is empty, inspect:

- The model response.
- The tool schemas in `agent/tools.py`.
- The system prompt in `agent/orchestrator.py`.

For final delivery, remove temporary debugging files and avoid committing raw API response dumps.

## Notes For Assignment Submission

The final submission should include:

- Source code.
- `requirements.txt`.
- This `README.md`.
- A generated triage output CSV for at least 200 tickets.
- A short technical document answering the assignment questionnaire.

Before submitting, clean local-only files such as:

- `.env`
- `.DS_Store`
- temporary API response dumps
- Python cache folders

The delivered CSV should contain at least 200 processed tickets and the required structured triage fields.
