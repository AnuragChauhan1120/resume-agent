from app.pipeline.parser import ParsedResume


class Chunk:
    def __init__(self, text: str, metadata: dict):
        self.text = text
        self.metadata = metadata  # which section, which resume, position


def chunk_resume(parsed: ParsedResume, filename: str) -> list[Chunk]:
    chunks = []
    
    for section_name, section_content in parsed.sections.items():
        if not section_content.strip():
            continue
        
        # Some sections stay as one chunk (skills, summary)
        if section_name in ["skills", "technical skills", "summary", "objective", "about", "header"]:
            chunks.append(Chunk(
                text=f"{section_name.upper()}:\n{section_content}",
                metadata={
                    "filename": filename,
                    "section": section_name,
                    "chunk_index": len(chunks),
                    "strategy": "whole_section"
                }
            ))
        
        # Others get split by entry (experience, projects)
        else:
            entry_chunks = _split_by_entry(section_content, section_name)
            for entry in entry_chunks:
                chunks.append(Chunk(
                    text=f"{section_name.upper()}:\n{entry}",
                    metadata={
                        "filename": filename,
                        "section": section_name,
                        "chunk_index": len(chunks),
                        "strategy": "by_entry"
                    }
                ))
    
    return chunks


# def _split_by_entry(text: str, section_name: str) -> list[str]:
#     """
#     Split a section into individual entries.
#     Entries are usually separated by blank lines in a resume.
#     """
#     # Split on double newlines — each entry is usually a separate block
#     raw_entries = text.split('\n\n')
    
#     entries = []
#     current = []
    
#     for block in raw_entries:
#         block = block.strip()
#         if not block:
#             continue
        
#         # If block is very short (like just a date or single word),
#         # it's probably part of the previous entry, not a new one
#         if len(block) < 30 and current:
#             current.append(block)
#         else:
#             if current:
#                 entries.append('\n\n'.join(current))
#             current = [block]
    
#     if current:
#         entries.append('\n\n'.join(current))
    
#     # If splitting produced nothing meaningful, return whole section as one chunk
#     if not entries:
#         return [text]
    
#     return entries

def _split_by_entry(text: str, section_name: str) -> list[str]:
    lines = text.split('\n')
    entries = []
    current = []
    current_length = 0
    MIN_CHUNK_CHARS = 150  # don't finalize a chunk until it has this much content

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        is_title_line = (
            len(stripped) < 60 and
            not stripped.endswith(('.', ',', ';', ':')) and
            not stripped[0].islower()
        )

        if is_title_line and current_length >= MIN_CHUNK_CHARS:
            entries.append('\n'.join(current))
            current = [stripped]
            current_length = len(stripped)
        else:
            current.append(stripped)
            current_length += len(stripped)

    if current:
        entries.append('\n'.join(current))

    # Merge any chunks that are still too small into the previous one
    merged = []
    for entry in entries:
        if merged and len(entry) < MIN_CHUNK_CHARS:
            merged[-1] = merged[-1] + '\n' + entry
        else:
            merged.append(entry)

    return merged if merged else [text]