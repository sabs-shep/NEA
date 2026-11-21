import os
import re
from typing import Any, cast
from llama_cpp import Llama


class AI:
    ### INITIALISATION
    def __init__(self):
        ## initial state
        self.context = {}
        self.preferences = {}
        self.knowledge_scope = []
        self.last_metadata = {}
        self.model: Llama | None = None

        ## model parameters (set in load_model)
        self.model_path = ""
        self.context_size = 2048
        self.threads = 4
        self.summary_percentage = 0.5
        self.max_tokens = 1024
        self.temperature = 0.7
        self.stop = ["###"]

    ### MODEL LOADING
    ## loads the llama model with validated configuration
    def load_model(self, config: dict):

        # path
        self.model_path = config.get("path")
        if not self.model_path:
            raise ValueError("config['path'] is required to load the model.")

        # context size
        try:
            self.context_size = int(config.get("context_size", 2048))
            if self.context_size <= 0 or self.context_size > 32768:
                self.context_size = 2048
        except Exception:
            self.context_size = 2048

        # threads
        try:
            self.threads = int(config.get("threads", 4))
            max_threads = os.cpu_count() or 4
            if self.threads <= 0 or self.threads > max_threads:
                self.threads = 4
        except Exception:
            self.threads = 4

        # summary percentage
        try:
            self.summary_percentage = float(config.get("summary_percentage", 0.5))
            if self.summary_percentage <= 0 or self.summary_percentage >= 1:
                self.summary_percentage = 0.5
        except Exception:
            self.summary_percentage = 0.5

        # temperature
        self.temperature = float(config.get("temperature", 0.7))

        # stop tokens
        self.stop = config.get("stop", ["###"])

        # compute max tokens (remaining context window)
        self.max_tokens = int(self.context_size * (1 - self.summary_percentage))
        if self.max_tokens < 32:
            self.max_tokens = 32

        # load llama model (CPU‑only)
        self.model = Llama(
            model_path=self.model_path,
            n_ctx=self.context_size,
            n_gpu_layers=0,
            n_threads=self.threads
        )

    ### CONTEXT
    def set_context(self, context_dict: dict):
        self.context.update(context_dict)

    def clear_context(self):
        self.context = {}

    ### CLEANING
    def _clean_ai_output(self, text: str) -> str:
        if not isinstance(text, str):
            text = str(text)

        # Remove everything before and including </think>
        if "</think>" in text:
            text = text.split("</think>", 1)[1]

        return text.strip()
    ### KNOWLEDGE
    def knowledge(self, scope=None):
        if scope is None:
            scope = []
        self.knowledge_scope = scope

    ### PREFERENCES
    def get_preferences(self) -> dict:
        return self.preferences

    def set_preferences(self, pref_dict: dict):
        self.preferences.update(pref_dict)

    ### GENERIC CALL
    ## sends a prompt to the model using explicit attributes
    def call(self, prompt: str) -> dict:

        if self.model is None:
            reply = f"[MODEL NOT LOADED] {prompt}"
            self.last_metadata = {
                "tokens_used": 0,
                "reasoning": "model not loaded",
                "context": self.context,
                "knowledge_scope": self.knowledge_scope
            }
            return {"reply": reply, "metadata": self.last_metadata}

        result = cast(dict[str, Any], self.model(
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            stop=self.stop,
            stream=False
        ))

        raw_reply = result["choices"][0]["text"]
        reply = self._clean_ai_output(raw_reply)

        self.last_metadata = {
            "tokens_used": result.get("usage", {}).get("total_tokens", 0),
            "reasoning": "llama_cpp call",
            "context": self.context,
            "knowledge_scope": self.knowledge_scope
        }

        return {"reply": reply, "metadata": self.last_metadata}

    ### CONTEXT CONDENSATION
    ## merges old context, user message, and assistant reply into a compressed summary
    def condense_context(self, old_context: str, user_message: str, assistant_reply: str) -> str:

        # compute token + char limits
        summary_token_limit = int(self.context_size * self.summary_percentage)
        summary_char_limit = summary_token_limit * 4

        # build summarisation prompt
        prompt = f"""
### SECTION 1: OLD CONTEXT
{old_context}

### SECTION 2: USER MESSAGE
{user_message}

### SECTION 3: ASSISTANT RESPONSE
{assistant_reply}

### TASK
Condense these into a single context summary.
If contradictions exist, Section 3 overrides Section 2, and Section 2 overrides Section 1.
The summary MUST NOT exceed {summary_token_limit} tokens.
Return ONLY the updated context summary.
""".strip()

        result = self.call(prompt)
        summary = result["reply"]

        # enforce hard character cutoff
        if len(summary) > summary_char_limit:
            summary = summary[:summary_char_limit].rsplit(" ", 1)[0]

        return summary

    ### THINK PASS
    ## performs a deep reasoning pass without updating context
    def think_pass(self, context_summary: str, user_message: str) -> str:
        prompt = f"""
### STABLE CONTEXT
{context_summary}

### QUESTION
{user_message}

### TASK
Rewrite the context so it contains ONLY what is needed to answer the question.

- Extract relevant facts
- Extract constraints or assumptions
- Create a clear, concise plan for answering the question
- Remove irrelevant information
- Do NOT explain your reasoning
- Do NOT answer the question

Return the result in this format:

FACTS:
- ...

CONSTRAINTS:
- ...

PLAN:
1. ...
2. ...
""".strip()

        result = self.call(prompt)
        return result["reply"]

    ### generates the final answer (with or without think mode)
    def answer_pass(self, context_or_think: str, user_message: str) -> str:

        prompt = f"""
### INPUT
{context_or_think}

### QUESTION
{user_message}

### TASK
Provide the final answer to the user's question.
Do NOT include chain‑of‑thought.
Return ONLY the answer.
If you feel as though you cannot answer the question based on the input, respond with:
"I do not have enough information to answer that question, I recomend using the search tool or doing external research."
""".strip()

        result = self.call(prompt)
        return result["reply"]

    ### SEARCH QUERY GENERATION
    ## generates 1–3 search queries for external lookup (e.g. Wikipedia)
    def generate_search_queries(self, user_question: str, max_queries: int = 3) -> list[str]:

        prompt = f"""
You are helping to generate search queries for external research on wikipedia.

### QUESTION
{user_question}

### TASK
Generate between 1 and {max_queries} concise search queries that would help answer the question.
Return ONLY the queries, one per line, with no bullets, numbering, or extra text.
""".strip()

        result = self.call(prompt)
        lines = [line.strip() for line in result["reply"].splitlines() if line.strip()]
        return lines[:max_queries]

    ### EXTERNAL INFO SUMMARISATION
    ## summarises external text into only the key points relevant to the question
    def summarise_external_info(self, user_question: str, info_text: str) -> str:

        # compute token + char limits for this summary
        summary_token_limit = int(self.context_size * self.summary_percentage)
        summary_char_limit = summary_token_limit * 4

        prompt = f"""
### QUESTION
{user_question}

### EXTERNAL INFORMATION
{info_text}

### TASK
Summarise ONLY the key facts from the external information that are directly useful
for answering the question. Remove irrelevant details, trivia, and formatting.
Keep the summary as compact as possible while preserving the important points.
Return ONLY the summary.
""".strip()

        result = self.call(prompt)
        summary = result["reply"]

        if len(summary) > summary_char_limit:
            summary = summary[:summary_char_limit].rsplit(" ", 1)[0]

        return summary

    ### NORMAL RESPONSE (legacy)
    def respond(self, context_summary: str, user_message: str) -> str:
        prompt = f"""
### CONTEXT
{context_summary}

### USER MESSAGE
{user_message}

### TASK
Respond to the user.
""".strip()

        result = self.call(prompt)
        return result["reply"]

    ### EXPLAIN
    def explain(self, last_call: bool = True) -> dict:
        return self.last_metadata

    ### SERIALISATION
    def to_json(self) -> dict:
        return {
            "context": self.context,
            "preferences": self.preferences,
            "knowledge_scope": self.knowledge_scope,
            "context_size": self.context_size,
            "threads": self.threads,
            "summary_percentage": self.summary_percentage,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stop": self.stop
        }

    def from_json(self, json_obj: dict):
        self.context = json_obj.get("context", {})
        self.preferences = json_obj.get("preferences", {})
        self.knowledge_scope = json_obj.get("knowledge_scope", [])


### RUN DIRECTLY
if __name__ == "__main__":
    from SettingsController import SettingsController

    settings = SettingsController("Settings")

    filename = settings.get_current("llm")
    if filename is None:
        raise ValueError("No 'llm' setting found or no model selected.")

    models_dir = os.path.join(settings.base_dir, "models")
    model_path = os.path.join(models_dir, filename)

    context_size = settings.get_current("context_size") or 2048
    threads = settings.get_current("threads") or 4
    summary_percentage = settings.get_current("summary_percentage") or 0.5
    temperature = settings.get_current("temperature") or 0.7

    ai = AI()
    ai.load_model({
        "path": model_path,
        "context_size": context_size,
        "threads": threads,
        "summary_percentage": summary_percentage,
        "temperature": temperature
    })

    print("Model:", model_path)
    print("Context size:", context_size)
    print("Threads:", threads)
    print("Running in CPU‑only mode.")