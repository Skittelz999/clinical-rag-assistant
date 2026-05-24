"""Safety and evidence guards for AI responses."""


def should_refuse_due_to_insufficient_evidence(retrieved_chunk_count: int) -> bool:
    return retrieved_chunk_count == 0
