import fitz  # this is pymupdf, confusingly imported as fitz
import re
from pathlib import Path


# --- Data structure for what we extract ---
# class ParsedResume:
#     def __init__(self, raw_text: str, sections: dict, metadata: dict):
#         self.raw_text = raw_text
#         self.sections = sections    # {"experience": "...", "skills": "..."}
#         self.metadata = metadata    # {"num_pages": 2, "filename": "..."}

class ParsedResume:      #added resume or not so that user knows at upload time and doesnt get errors later on (tried)
    def __init__(self, raw_text: str, sections: dict, metadata: dict, doc_type: str = "unknown"):
        self.raw_text = raw_text
        self.sections = sections
        self.metadata = metadata
        # self.doc_type = doc_type  # "resume" or "other"

# --- Main parser ---
def parse_resume(file_path: str) -> ParsedResume:
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"No file at {file_path}")
    
    doc = fitz.open(file_path)
    num_pages = len(doc)
    # Step 1: extract raw text page by page
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()
    

    doc.close()
    
    # Step 2: clean it up
    cleaned = _clean_text(raw_text)
    
    # Step 3: detect sections
    sections = _extract_sections(cleaned)
    
    metadata = {
        "filename": path.name,
        "num_pages": num_pages,  # fitz keeps page count even after close
        "char_count": len(cleaned)
    }
    
    return ParsedResume(raw_text=cleaned, sections=sections, metadata=metadata)


def _clean_text(text: str) -> str:
    # Remove excessive whitespace and blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)   # 3+ newlines → 2
    text = re.sub(r'[ \t]+', ' ', text)       # multiple spaces → one
    text = text.strip()
    return text


def _extract_sections(text: str) -> dict:
    # Common resume section headers
    section_headers = [
        "experience", "work experience", "employment",
        "education", "academic",
        "skills", "technical skills",
        "projects",
        "certifications", "achievements",
        "summary", "objective", "about",
        "extra curriculars", "extracurricular", "activities"
    ]
    
    sections = {}
    lines = text.split('\n')
    
    current_section = "header"   # text before first section = header (usually name/contact)
    current_content = []
    
    for line in lines:
        line_lower = line.strip().lower()
        
        # Check if this line is a section header
        matched_section = None
        for header in section_headers:
            if line_lower.startswith(header) and len(line_lower) < 40:
                matched_section = header
                break
        
        if matched_section:
            # Save previous section
            sections[current_section] = '\n'.join(current_content).strip()
            current_section = matched_section
            current_content = []
        else:
            current_content.append(line)
    
    # Don't forget the last section
    sections[current_section] = '\n'.join(current_content).strip()
    
    # Remove empty sections
    sections = {k: v for k, v in sections.items() if v}
    
    return sections

def _clean_text(text: str) -> str:
    lines = text.split('\n')
    joined = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            joined.append('')
            continue
        
        # If previous line doesn't end with sentence-ending punctuation
        # and current line starts lowercase or with punctuation — it's a continuation
        if (joined and joined[-1] and
            not joined[-1].endswith(('.', '?', '!', ':', '–', '—')) and
            (stripped[0].islower() or stripped[0] in '(,;)')):
            joined[-1] = joined[-1] + ' ' + stripped
        else:
            joined.append(stripped)
    
    text = '\n'.join(joined)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()