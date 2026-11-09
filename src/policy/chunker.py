"""Policy chunking engine with rich metadata preservation."""

from __future__ import annotations

from src.policy.schemas import PolicyChunk, StructuredPolicy


class PolicyChunker:
    """Splits policy documents into semantically coherent chunks with search metadata."""

    def __init__(self, max_chunk_chars: int = 800, overlap_chars: int = 100):
        self.max_chunk_chars = max_chunk_chars
        self.overlap_chars = overlap_chars

    def chunk_policy(self, policy: StructuredPolicy) -> list[PolicyChunk]:
        chunks: list[PolicyChunk] = []
        chunk_idx = 0

        # Chunk 1: Policy overview / summary chunk
        summary_text = (
            f"Policy: {policy.title} ({policy.id})\n"
            f"Payer: {policy.payer} | Type: {policy.policy_type} | Code(s): {', '.join(policy.cpt_codes)}\n"
            f"Procedure: {policy.procedure_name}\n"
            f"Summary: {policy.summary}"
        )
        chunks.append(
            PolicyChunk(
                chunk_id=f"{policy.id}-chunk-{chunk_idx:02d}",
                policy_id=policy.id,
                procedure_name=policy.procedure_name,
                payer=policy.payer,
                section_title="Policy Overview & Summary",
                cpt_codes=policy.cpt_codes,
                content=summary_text,
                chunk_index=chunk_idx,
                metadata={
                    "source_url": policy.source_url,
                    "effective_date": policy.effective_date,
                    "icd10_codes": policy.icd10_codes,
                },
            )
        )
        chunk_idx += 1

        # Section-level chunks
        for section in policy.sections:
            content = section.content.strip()
            if len(content) <= self.max_chunk_chars:
                chunk_text = (
                    f"Policy: {policy.title} | Procedure: {policy.procedure_name}\n"
                    f"Section: {section.title}\n"
                    f"{content}"
                )
                chunks.append(
                    PolicyChunk(
                        chunk_id=f"{policy.id}-chunk-{chunk_idx:02d}",
                        policy_id=policy.id,
                        procedure_name=policy.procedure_name,
                        payer=policy.payer,
                        section_title=section.title,
                        cpt_codes=policy.cpt_codes,
                        content=chunk_text,
                        chunk_index=chunk_idx,
                        metadata={"section": section.title},
                    )
                )
                chunk_idx += 1
            else:
                # Sliding window split across paragraphs or lines
                lines = content.split("\n")
                current_block: list[str] = []
                current_len = 0

                for line in lines:
                    line_len = len(line)
                    if current_len + line_len > self.max_chunk_chars and current_block:
                        block_text = "\n".join(current_block)
                        chunk_text = (
                            f"Policy: {policy.title} | Procedure: {policy.procedure_name}\n"
                            f"Section: {section.title}\n"
                            f"{block_text}"
                        )
                        chunks.append(
                            PolicyChunk(
                                chunk_id=f"{policy.id}-chunk-{chunk_idx:02d}",
                                policy_id=policy.id,
                                procedure_name=policy.procedure_name,
                                payer=policy.payer,
                                section_title=section.title,
                                cpt_codes=policy.cpt_codes,
                                content=chunk_text,
                                chunk_index=chunk_idx,
                                metadata={"section": section.title},
                            )
                        )
                        chunk_idx += 1
                        current_block = [line]
                        current_len = line_len
                    else:
                        current_block.append(line)
                        current_len += line_len + 1

                if current_block:
                    block_text = "\n".join(current_block)
                    chunk_text = (
                        f"Policy: {policy.title} | Procedure: {policy.procedure_name}\n"
                        f"Section: {section.title}\n"
                        f"{block_text}"
                    )
                    chunks.append(
                        PolicyChunk(
                            chunk_id=f"{policy.id}-chunk-{chunk_idx:02d}",
                            policy_id=policy.id,
                            procedure_name=policy.procedure_name,
                            payer=policy.payer,
                            section_title=section.title,
                            cpt_codes=policy.cpt_codes,
                            content=chunk_text,
                            chunk_index=chunk_idx,
                            metadata={"section": section.title},
                        )
                    )
                    chunk_idx += 1

        return chunks
