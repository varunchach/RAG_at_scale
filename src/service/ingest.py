import io
import re
from pathlib import Path


def _extract_pdf_text(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(file_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    text = re.sub(r'\s+', ' ', text).strip()
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start:start + chunk_size].strip())
        start += chunk_size - overlap
    return [c for c in chunks if len(c) > 30]


def pdf_to_chunks(file_bytes: bytes, filename: str,
                  chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    text = _extract_pdf_text(file_bytes)
    chunks = _chunk_text(text, chunk_size, overlap)
    stem = Path(filename).stem
    return [{"id": f"{stem}_chunk{i}", "content": chunk}
            for i, chunk in enumerate(chunks)]
