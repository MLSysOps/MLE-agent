from itertools import islice
from mem0 import Memory
from mem0.configs.base import MemoryConfig

from mle.model import openai


class Mem0:

    def __init__(self):
        cfg = MemoryConfig()
        self._memory = Memory.from_config(cfg)

    def add(self, content: object | str, metadata: dict[str, str]):
        """
        Adds content to memory. Content can be non-text (e.g., debug/programming sessions).
        Args:
          - content: the item to be memorized
          - metadata: additional context or tags to guide mem0 LLM retrieval
        """
        if not isinstance(content, (str, list[dict[str, str]])):
            assert hasattr(content, "__str__")
            content = str(content)
        self._memory.add(content, metadata=metadata, infer=False)

    def query(self, content: str, limit_size: int = 5, fast_query: bool = False):
        """
        Retrieves relevant memories based on a query.
        Args:
          - content: input query text
          - limit_size: max number of results
          - fast_query: uses vector DB with consolidated memory for faster response
        """
        if fast_query:
            # search only vector store for fast query
            self._memory._search_vector_store(content, limit=limit_size)
        return self._memory.graph.search(content, limit=limit_size)

    def evict(self, conditions: list):
        """
        Removes stale or redundant memories based on user-defined conditions.
        """
        raise NotImplemented

    def mem_consolidation(
        self,
        system_prompt: str | None = None,
        *,
        model: str = "gpt-4o-mini",
        batch_size: int = 20,
        temperature: float = 0.2,
    ):
        """
        Reads *all* nodes from the graph DB, asks an OpenAI chat model to
        compress / summarize them in small batches, and pushes the summaries
        into the vector DB so future queries hit the lighter‑weight embeddings.

        Args
        ----
        system_prompt   – Optional system prompt that frames the summarizer’s role.
                          If None, a sensible default is supplied.
        model           – Any chat‑completion model (defaults to GPT‑4o mini).
        batch_size      – How many raw memory nodes to feed the model at once.
        temperature     – Sampling temperature; keep it low for factual recall.
        """
        if system_prompt is None:
            system_prompt = (
                "You are mem0's consolidation assistant. Read the raw memory "
                "items below and rewrite them as a short, information‑dense "
                "capsule suitable for retrieval. Preserve key facts, drop noise."
            )

        # 1) Grab every memory node from the graph store
        raw_nodes = self._memory.graph.get_all()          # → Iterable[dict]
        raw_texts = [n["content"] for n in raw_nodes if n.get("content")]

        # Helper to iterate in fixed‑size chunks
        def batched(iterable, n):
            it = iter(iterable)
            while True:
                chunk = list(islice(it, n))
                if not chunk:
                    break
                yield chunk

        for chunk in batched(raw_texts, batch_size):
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Below is a batch of raw memory entries delimited by\n"
                        "```text\n" + "\n".join(chunk) + "\n```"
                        "\nSummarize them into a concise, standalone paragraph."
                    ),
                },
            ]
            rsp = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            summary = rsp.choices[0].message.content.strip()

            self._memory.add(
                summary,
                metadata={
                    "src": "consolidation",
                    "batch_size": str(len(chunk)),
                },
                infer=True,
            )

        return {"raw_items": len(raw_texts), "batches": (len(raw_texts) + batch_size - 1) // batch_size}
