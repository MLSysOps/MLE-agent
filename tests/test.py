from mle.utils.memory import Mem0, LanceDBMemory, HybridMemory


chat_sessions: list[dict[str, str]] = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "assistant", "content": "What is your favorite city?"},
    {"role": "user", "content": "The capital of France, Paris."},
    {"role": "assistant", "content": "Sure, I will remember for these"},
]
metadata = {"HITL-score": 1.0, "Eval-score": 99.1}

slow_mem = Mem0()
fast_mem = LanceDBMemory("./")

slow_mem.reset()
fast_mem.reset()

hybrid_mem = HybridMemory(slow_mem, fast_mem)

hybrid_mem.add(chat_sessions, metadata=metadata, prompt="summary all information")
hybrid_mem.last_n_consolidate(last_n=1)
hybrid_mem.topk_consolidate(k=1, metadata_key="HITL-score")

print(hybrid_mem.query("what is the user's favorite city?", n_results=1)[0][0]["text"])
