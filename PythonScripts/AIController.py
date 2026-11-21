import json
import os
import urllib.parse
import urllib.request
import re

from AI import AI
from Controller import Controller
from SettingsController import SettingsController


class AIController(Controller):

    ### INITIALISATION
    def __init__(self, name="AI", conversation_id="default"):
        super().__init__(name)

        ## controllers
        self.settings = SettingsController("Settings")
        self.ai = AI()
        self.context_summary = ""
        self.conversation_id = conversation_id

        # ### KB CONTEXT (MERGED INTO SUMMARY)
        self.kb_context = None

        ### load model
        filename = self.settings.get_current("llm")
        if filename is None:
            raise ValueError("No LLM selected in settings.json")

        models_dir = os.path.join(self.base_dir, "models")
        model_path = os.path.join(models_dir, filename)

        ## pull current settings
        context_size = self.settings.get_current("context_size")
        threads = self.settings.get_current("threads")
        summary_percentage = self.settings.get_current("summary_percentage")
        temperature = self.settings.get_current("temperature")

        ## fallback to defaults if missing
        if context_size is None:
            context_size = self.settings._preferences["context_size"]["default"]

        if threads is None:
            threads = self.settings._preferences["threads"]["default"]

        if summary_percentage is None:
            summary_percentage = 0.5

        if temperature is None:
            temperature = 0.7

        ## attempt model load with fallback to defaults
        try:
            self.ai.load_model({
                "path": model_path,
                "context_size": context_size,
                "threads": threads,
                "summary_percentage": summary_percentage,
                "temperature": temperature
            })
        except Exception as e:
            self.log(f"Model load failed, reverting to default settings: {e}")

            default_ctx = self.settings._preferences["context_size"]["default"]
            default_threads = self.settings._preferences["threads"]["default"]

            self.ai.load_model({
                "path": model_path,
                "context_size": default_ctx,
                "threads": default_threads,
                "summary_percentage": summary_percentage,
                "temperature": temperature
            })

        ### conversation file path
        self.conversation_dir = os.path.join(self.base_dir, "conversations")
        os.makedirs(self.conversation_dir, exist_ok=True)

        self.file_path = os.path.join(
            self.conversation_dir,
            f"{conversation_id}.json"
        )

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

        self.log(f"AIController initialised for conversation '{conversation_id}'")

    ### APPEND TO JSON FILE
    def append_to_file(self, role, content):
        try:
            with open(self.file_path, "r") as f:
                data = json.load(f)
        except Exception:
            data = []

        data.append({"role": role, "content": content})

        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

        self.log(f"Appended {role} message to conversation file.")

    def set_conversation_id(self, conversation_id):
        self.conversation_id = conversation_id

        # rebuild file path
        self.file_path = os.path.join(
            self.conversation_dir,
            f"{conversation_id}.json"
        )

        # ensure file exists
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w") as f:
                json.dump([], f)

        self.log(f"Conversation switched to '{conversation_id}'.")

    def load_kb_context(self, context_text):
        """
        C# sends a fully formatted string.
        AIController simply merges it into the rolling context.
        """
        try:
            if not isinstance(context_text, str):
                context_text = str(context_text)

            self.context_summary = self.ai.condense_context(
                self.context_summary,
                "KB CONTEXT",
                context_text
            )

            self.log("KB context merged into summary.")

        except Exception as e:
            self.log(f"Failed to load KB context: {e}")

    ### SIMPLE WIKIPEDIA FETCH
    def _fetch_simple_wikipedia(self, search_query: str) -> dict:
        try:
            search_url = "https://simple.wikipedia.org/w/api.php"

            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": search_query,
                "srlimit": 1,
            }

            url = f"{search_url}?{urllib.parse.urlencode(search_params)}"
            with urllib.request.urlopen(url, timeout=5) as response:
                search_data = json.loads(response.read().decode())

            if not search_data.get("query", {}).get("search"):
                return {
                    "status": "error",
                    "message": f"No Simple Wikipedia article found for '{search_query}'",
                }

            normalized_title = search_data["query"]["search"][0]["title"]

            content_params = {
                "action": "query",
                "format": "json",
                "titles": normalized_title,
                "prop": "extracts",
                "exintro": "true",
                "explaintext": "true",
                "redirects": 1,
            }

            url = f"{search_url}?{urllib.parse.urlencode(content_params)}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read().decode())

            pages = data["query"]["pages"]
            page_id = list(pages.keys())[0]

            if page_id == "-1":
                return {
                    "status": "error",
                    "message": f"No Simple Wikipedia article found for '{search_query}'",
                }

            content = pages[page_id].get("extract", "").strip()
            if not content:
                return {
                    "status": "error",
                    "message": f"Empty Simple Wikipedia article for '{search_query}'",
                }

            return {
                "status": "success",
                "content": content,
                "title": pages[page_id]["title"],
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}

    ### TEXT CHUNKING
    def _chunk_text(self, text: str, max_chars: int = 2000) -> list[str]:
        if len(text) <= max_chars:
            return [text]

        chunks: list[str] = []
        current: list[str] = []

        for paragraph in text.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph) > max_chars:
                start = 0
                while start < len(paragraph):
                    end = start + max_chars
                    chunks.append(paragraph[start:end])
                    start = end
            else:
                candidate = ("\n\n".join(current) + "\n\n" + paragraph) if current else paragraph
                if len(candidate) <= max_chars:
                    current.append(paragraph)
                else:
                    if current:
                        chunks.append("\n\n".join(current))
                    current = [paragraph]

        if current:
            chunks.append("\n\n".join(current))

        return chunks

    ### WIKIPEDIA RETRIEVAL + SUMMARISATION
    def _retrieve_and_enrich(self, user_input: str):
        self.log("Search enabled — running retrieval pipeline.")

        try:
            search_queries = self.ai.generate_search_queries(user_input)
            self.log(f"AI-generated search queries: {search_queries}")
        except Exception as e:
            self.log(f"Search query generation failed: {e}")
            return

        if not search_queries:
            self.log("No search queries generated; skipping retrieval.")
            return

        combined_text = ""
        for query in search_queries:
            result = self._fetch_simple_wikipedia(query)
            if result.get("status") != "success":
                self.log(f"Search fetch failed for '{query}': {result.get('message')}")
                continue

            title = result.get("title", query)
            content = result.get("content", "")
            if not content:
                continue

            combined_text += f"\n\n### {title}\n{content}"

        if not combined_text.strip():
            self.log("No usable search content retrieved; skipping enrichment.")
            return

        chunks = self._chunk_text(combined_text, max_chars=2000)

        try:
            if len(chunks) == 1:
                search_summary = self.ai.summarise_external_info(user_input, chunks[0])
            else:
                partial_summaries = []
                for idx, chunk in enumerate(chunks):
                    self.log(f"Summarising search chunk {idx + 1}/{len(chunks)}")
                    partial = self.ai.summarise_external_info(user_input, chunk)
                    if partial and partial.strip():
                        partial_summaries.append(partial)

                if not partial_summaries:
                    self.log("All chunk summaries were empty; skipping enrichment.")
                    return

                combined_summaries = "\n\n".join(partial_summaries)
                search_summary = self.ai.summarise_external_info(user_input, combined_summaries)
        except Exception as e:
            self.log(f"Search summarisation failed: {e}")
            return

        if not search_summary or not search_summary.strip():
            self.log("Search summary was empty; skipping enrichment.")
            return

        try:
            self.context_summary = self.ai.condense_context(
                self.context_summary,
                "SEARCH RESULTS",
                search_summary
            )
            self.log("Context summary enriched with search results.")
        except Exception as e:
            self.log(f"Failed to merge search results into context: {e}")

    ### SEND MESSAGE (SEARCH → THINK → ANSWER)
    def send_message(self, user_input, think: bool = False, search: bool = False):

        ## PYTHON.NET ARGUMENT NORMALISATION
        try:
            if hasattr(user_input, "__len__") and not isinstance(user_input, str):
                items = list(user_input)

                if len(items) == 3:
                    user_input, think, search = items
                elif len(items) == 1:
                    user_input = items[0]
        except Exception:
            pass

        user_input = str(user_input)

        self.log(f"User message received: {user_input}")
        self.append_to_file("user", user_input)

        if search:
            self._retrieve_and_enrich(user_input)

        # EFFECTIVE CONTEXT = rolling summary (KB already merged)
        effective_context = self.context_summary or ""

        # THINK STAGE
        if think:
            self.log("Think mode enabled — running think pass.")
            think_output = self.ai.think_pass(effective_context, user_input)
            answer_input = think_output if think_output else effective_context
        else:
            answer_input = effective_context

        if answer_input is None:
            answer_input = ""

        # ANSWER STAGE
        reply = self.ai.answer_pass(answer_input, user_input)
        reply = str(reply)

        self.append_to_file("assistant", reply)
        self.log("Assistant reply generated and saved.")

        # CONTEXT UPDATE
        self.context_summary = self.ai.condense_context(
            self.context_summary,
            user_input,
            reply
        )

        self.log("Context summary updated.")

        return reply

    ### CONTEXT
    def set_context(self, context_text: str):
        self.context_summary = context_text
        self.log("Context updated via set_context().")

    def clear_context(self):
        self.context_summary = ""
        self.log("Context cleared.")

    ### KNOWLEDGE
    def attach_knowledge(self, knowledge_entry):
        self.ai.knowledge(knowledge_entry)
        self.log("Knowledge scope updated.")

    ### HISTORY
    def get_history(self):
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    ### EXPLAIN
    def explain_last(self):
        return self.ai.explain()