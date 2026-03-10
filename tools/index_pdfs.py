#!/usr/bin/env python3
"""
index_pdfs.py
────────────────────────────────────────────────────────────────────
Create a **fresh** ChromaDB vector-index from PDFs using semantic chunking,
table extraction, and rich metadata for optimal RAG performance.

High-level flow
---------------
1. **Reset DB** – delete any existing ChromaDB folder for a clean start.
2. **Collect PDFs** – scan the specified directory for *.pdf files.
3. **Extract content** – use PyMuPDF (fitz) to extract text and tables with
   page-level granularity. PyMuPDF is chosen for security, performance, and
   active maintenance.
4. **Semantic chunking** – split text into meaningful chunks (~500-1000 chars)
   with overlap (~200 chars) to preserve context across chunk boundaries.
5. **Table handling** – extract and preserve table structure separately.
6. **Embed** – convert each chunk to a 384-dimensional vector (MiniLM-L6-v2).
7. **Store** – write `(vector, text, metadata)` into a persistent Chroma
   collection called `"pdf_documents"`.

Security Notes
--------------
PyMuPDF (fitz) is used instead of pdfplumber because:
- More actively maintained with regular security updates
- Better performance for large documents
- Superior table extraction capabilities
- Robust handling of complex PDF structures

Usage
-----
python index_pdfs.py [--pdf-dir PATH] [--chroma-path PATH] [--chunk-size SIZE]

Arguments:
  --pdf-dir       Directory containing PDF files (default: ./knowledge_base_pdfs)
  --chroma-path   Output ChromaDB directory (default: ./chroma_db)
  --chunk-size    Target chunk size in characters (default: 800)
  --chunk-overlap Overlap between chunks in characters (default: 200)
  --collection    ChromaDB collection name (default: pdf_documents)
"""

# ───────────────────── standard-library imports ────────────────────
import argparse
import shutil
import re
from pathlib import Path
from typing import List, Dict, Any
import logging

# ───────────────────── 3rd-party imports ───────────────────────────
# All imports have graceful error handling with installation instructions

try:
    import fitz  # PyMuPDF - secure and performant PDF parser
except ImportError:
    print("ERROR: PyMuPDF not installed. Install with: pip install pymupdf")
    exit(1)

try:
    # SentenceTransformer converts text to vector embeddings
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
    exit(1)

try:
    # ChromaDB is our vector database for storing and querying embeddings
    from chromadb import PersistentClient
    from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
except ImportError:
    print("ERROR: chromadb not installed. Install with: pip install chromadb")
    exit(1)

# ───────────────────── logging setup ───────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ╔════════════════════════════════════════════════════════════════╗
# 1.  Configuration / constants                                    ║
# ╚════════════════════════════════════════════════════════════════╝

# Default directory containing PDF files to index
DEFAULT_PDF_DIR = Path("./knowledge_base_pdfs")

# Default output directory for ChromaDB vector database
DEFAULT_CHROMA_PATH = Path("./chroma_db")

# Default collection name (like a table name in SQL)
DEFAULT_COLLECTION_NAME = "pdf_documents"

# Embedding model from HuggingFace
# all-MiniLM-L6-v2: Fast, 384-dim vectors, good balance of speed and quality
DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"

# Default chunk size in characters
# 800 chars ≈ 1-2 paragraphs, good for capturing complete thoughts
DEFAULT_CHUNK_SIZE = 800

# Default overlap between chunks in characters
# 200 chars overlap ensures context continuity across chunk boundaries
DEFAULT_CHUNK_OVERLAP = 200

# ╔════════════════════════════════════════════════════════════════╗
# 2.  Text chunking with semantic awareness                        ║
# ╚════════════════════════════════════════════════════════════════╝

def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE,
               overlap: int = DEFAULT_CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks while trying to preserve sentence boundaries.

    Overlap ensures that context isn't lost at chunk boundaries, which is critical
    for RAG performance.

    Parameters
    ----------
    text : str
        The text to chunk.
    chunk_size : int
        Target size of each chunk in characters.
    overlap : int
        Number of characters to overlap between chunks.

    Returns
    -------
    List[str]
        List of text chunks with overlap.
    """
    # Handle edge case: if text is already small enough, return as-is
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []

    # Split on sentence boundaries (., !, ?) followed by whitespace
    # This preserves semantic meaning better than arbitrary character splits
    sentences = re.split(r'(?<=[.!?])\s+', text)

    current_chunk = ""
    for sentence in sentences:
        # Check if adding this sentence would exceed our target chunk size
        if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
            # Save the current chunk
            chunks.append(current_chunk.strip())

            # Start new chunk with overlap from end of previous chunk
            # This ensures context continuity across chunk boundaries
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            current_chunk = overlap_text + " " + sentence
        else:
            # Keep building the current chunk
            current_chunk += (" " if current_chunk else "") + sentence

    # Don't forget to add the final chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks


def extract_tables_from_page(page: fitz.Page) -> List[Dict[str, Any]]:
    """
    Extract tables from a PDF page using PyMuPDF's table detection.

    Parameters
    ----------
    page : fitz.Page
        The PDF page to extract tables from.

    Returns
    -------
    List[Dict[str, Any]]
        List of tables, each with 'rows' and 'text' representation.
    """
    tables = []
    try:
        # Use PyMuPDF's built-in table detection algorithm
        # This automatically identifies table structures based on layout
        table_finder = page.find_tables()

        if table_finder.tables:
            # Process each detected table on the page
            for table_idx, table in enumerate(table_finder.tables):
                # Extract table as a 2D list (rows and columns)
                table_data = table.extract()

                if table_data:
                    # Convert table to human-readable text format
                    # Each cell is separated by " | " and rows by newlines
                    table_text = "\n".join([
                        " | ".join([str(cell) if cell else "" for cell in row])
                        for row in table_data
                    ])

                    # Wrap table text with markers so LLM knows it's a table
                    tables.append({
                        "index": table_idx,
                        "rows": table_data,  # Original structured data
                        "text": f"[TABLE]\n{table_text}\n[/TABLE]"  # Text for embedding
                    })
    except Exception as e:
        # Table extraction is best-effort; log warning but continue
        logger.warning(f"Could not extract tables: {e}")

    return tables


def extract_content_from_pdf(pdf_path: Path, chunk_size: int,
                             chunk_overlap: int) -> List[Dict[str, Any]]:
    """
    Extract text and tables from a PDF with rich metadata.

    Parameters
    ----------
    pdf_path : Path
        Path to the PDF file.
    chunk_size : int
        Target chunk size in characters.
    chunk_overlap : int
        Overlap between chunks in characters.

    Returns
    -------
    List[Dict[str, Any]]
        List of chunks, each with 'text', 'metadata', and 'type' fields.
    """
    chunks = []

    try:
        # Open the PDF file using PyMuPDF
        doc = fitz.open(pdf_path)

        # Process each page in the PDF
        for page_num, page in enumerate(doc, start=1):
            # ═══════════════════════════════════════════════════════════
            # STEP 1: Extract tables from this page
            # ═══════════════════════════════════════════════════════════
            # Tables are processed separately to preserve their structure
            tables = extract_tables_from_page(page)

            # Create a separate chunk for each table found
            for table in tables:
                chunks.append({
                    "text": table["text"],  # Formatted table text with [TABLE] markers
                    "metadata": {
                        "source": str(pdf_path.name),  # Filename for citation
                        "page": page_num,              # Page number for reference
                        "type": "table",               # Mark as table for filtering
                        "table_index": table["index"]  # Which table on this page
                    },
                    "type": "table"
                })

            # ═══════════════════════════════════════════════════════════
            # STEP 2: Extract regular text content from this page
            # ═══════════════════════════════════════════════════════════
            page_text = page.get_text("text")

            # Note: This extracts ALL text, including table text
            # For better quality, you could subtract table regions
            # but that requires more complex geometric calculations
            if page_text and page_text.strip():
                # Split page text into semantic chunks with overlap
                page_chunks = chunk_text(page_text, chunk_size, chunk_overlap)

                # Create a separate chunk entry for each text chunk
                for chunk_idx, chunk in enumerate(page_chunks):
                    if chunk.strip():  # Skip empty chunks
                        chunks.append({
                            "text": chunk,  # The actual text content
                            "metadata": {
                                "source": str(pdf_path.name),           # Filename
                                "page": page_num,                       # Page number
                                "type": "text",                         # Mark as text
                                "chunk_index": chunk_idx,               # Order on page
                                "total_chunks_on_page": len(page_chunks) # Context
                            },
                            "type": "text"
                        })

        # Get page count before closing (needed for logging)
        page_count = len(doc)

        # Clean up: close the PDF document
        doc.close()
        logger.info(f"Extracted {len(chunks)} chunks from {pdf_path.name} ({page_count} pages)")

    except Exception as e:
        logger.error(f"Failed to extract content from {pdf_path}: {e}")

    return chunks


def reset_chroma(db_path: Path) -> None:
    """
    Delete any existing ChromaDB directory to ensure a clean start.

    This prevents mixing embeddings from different runs, which could cause
    inconsistencies in retrieval results.

    Parameters
    ----------
    db_path : Path
        Path to the ChromaDB directory.
    """
    if db_path.exists():
        logger.info(f"Removing existing database at {db_path}")
        # Recursively delete the entire directory tree
        shutil.rmtree(db_path)

    # Create fresh directory (including parent directories if needed)
    db_path.mkdir(parents=True, exist_ok=True)


# ╔════════════════════════════════════════════════════════════════╗
# 3.  Main indexing routine                                        ║
# ╚════════════════════════════════════════════════════════════════╝

def index_pdfs(pdf_dir: Path, chroma_path: Path, collection_name: str,
               chunk_size: int, chunk_overlap: int) -> None:
    """
    Index all PDFs in the specified directory into ChromaDB.

    Parameters
    ----------
    pdf_dir : Path
        Directory containing PDF files.
    chroma_path : Path
        Output directory for ChromaDB.
    collection_name : str
        Name of the ChromaDB collection.
    chunk_size : int
        Target chunk size in characters.
    chunk_overlap : int
        Overlap between chunks in characters.
    """
    # ══════════════════════════════════════════════════════════════
    # SETUP PHASE: Initialize all components before processing
    # ══════════════════════════════════════════════════════════════

    # ── 1. Find PDF files ─────────────────────────────────────────
    # Scan the directory for all .pdf files and sort alphabetically
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        logger.error(f"No PDF files found in {pdf_dir.resolve()}")
        return

    logger.info(f"Found {len(pdf_files)} PDF files in {pdf_dir.resolve()}")

    # ── 2. Load embedding model ───────────────────────────────────
    # This downloads the model on first run (cached afterward)
    # all-MiniLM-L6-v2 produces 384-dimensional vectors
    logger.info(f"Loading embedding model: {DEFAULT_EMBED_MODEL}")
    try:
        embed_model = SentenceTransformer(DEFAULT_EMBED_MODEL)
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return

    # ── 3. Fresh ChromaDB ─────────────────────────────────────────
    # Delete old database if it exists to start clean
    # This prevents mixing old and new embeddings
    reset_chroma(chroma_path)

    # ── 4. Connect to ChromaDB ────────────────────────────────────
    # Create a persistent database that survives program restarts
    try:
        client = PersistentClient(
            path=str(chroma_path),      # Where to store the database on disk
            settings=Settings(),         # Use default settings
            tenant=DEFAULT_TENANT,       # Use default tenant
            database=DEFAULT_DATABASE,   # Use default database
        )
        # Get or create the collection (like a table in SQL)
        coll = client.get_or_create_collection(collection_name)
        logger.info(f"Created collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to create ChromaDB client: {e}")
        return

    # ── 5. Process each PDF ───────────────────────────────────────
    total_chunks = 0  # Track total across all PDFs for reporting

    for pdf_path in pdf_files:
        logger.info(f"Processing: {pdf_path.name}")

        # ═══════════════════════════════════════════════════════════
        # STEP A: Extract and chunk the PDF content
        # ═══════════════════════════════════════════════════════════
        # This gets us a list of chunks with text and metadata
        chunks = extract_content_from_pdf(pdf_path, chunk_size, chunk_overlap)

        if not chunks:
            logger.warning(f"No content extracted from {pdf_path.name}")
            continue

        # ═══════════════════════════════════════════════════════════
        # STEP B: Embed and store chunks in batches
        # ═══════════════════════════════════════════════════════════
        # Processing in batches of 100 prevents memory issues with large PDFs
        batch_size = 100

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]  # Get next batch of chunks

            # Pull out just the text content for embedding
            texts = [chunk["text"] for chunk in batch]

            # ─────────────────────────────────────────────────────
            # Generate vector embeddings for this batch
            # ─────────────────────────────────────────────────────
            # SentenceTransformer converts each text into a 384-dim vector
            try:
                embeddings = embed_model.encode(texts, show_progress_bar=False)
                # Convert numpy arrays to lists for ChromaDB
                embeddings_list = [emb.tolist() for emb in embeddings]
            except Exception as e:
                logger.error(f"Failed to generate embeddings: {e}")
                continue

            # ─────────────────────────────────────────────────────
            # Create unique IDs for each chunk
            # ─────────────────────────────────────────────────────
            # Format: "filename_chunk_123" for easy identification
            ids = [f"{pdf_path.stem}_chunk_{total_chunks + i + j}"
                   for j in range(len(batch))]

            # ─────────────────────────────────────────────────────
            # Extract metadata (source, page, type, etc.)
            # ─────────────────────────────────────────────────────
            # This enables filtering and citation in RAG queries
            metadatas = [chunk["metadata"] for chunk in batch]

            # ─────────────────────────────────────────────────────
            # Store everything in ChromaDB
            # ─────────────────────────────────────────────────────
            # Each entry has: unique ID, vector embedding, text, and metadata
            try:
                coll.add(
                    ids=ids,                    # Unique identifier for each chunk
                    embeddings=embeddings_list, # 384-dim vectors for similarity search
                    documents=texts,            # Original text for retrieval
                    metadatas=metadatas        # Source, page, type, etc.
                )
            except Exception as e:
                logger.error(f"Failed to add chunks to ChromaDB: {e}")
                continue

        # Update running total and log progress
        total_chunks += len(chunks)
        logger.info(f"  → Indexed {len(chunks)} chunks from {pdf_path.name}")

    logger.info(f"\n{'='*60}")
    logger.info(f"Indexing complete!")
    logger.info(f"  Total PDFs processed: {len(pdf_files)}")
    logger.info(f"  Total chunks indexed: {total_chunks}")
    logger.info(f"  Database location: {chroma_path.resolve()}")
    logger.info(f"  Collection name: {collection_name}")
    logger.info(f"{'='*60}\n")


# ╔════════════════════════════════════════════════════════════════╗
# 4.  CLI entry point                                              ║
# ╚════════════════════════════════════════════════════════════════╝

def main():
    """Parse command-line arguments and run the indexing process."""
    # ══════════════════════════════════════════════════════════════
    # Setup command-line argument parser
    # ══════════════════════════════════════════════════════════════
    parser = argparse.ArgumentParser(
        description="Index PDF files into ChromaDB for RAG applications.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default directories
  python index_pdfs.py

  # Specify custom PDF directory
  python index_pdfs.py --pdf-dir /path/to/pdfs

  # Customize chunk size and overlap
  python index_pdfs.py --chunk-size 1000 --chunk-overlap 250

  # Full customization
  python index_pdfs.py --pdf-dir ./data --chroma-path ./my_db --chunk-size 600
        """
    )

    # ── Input/Output paths ────────────────────────────────────────
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=DEFAULT_PDF_DIR,
        help=f"Directory containing PDF files (default: {DEFAULT_PDF_DIR})"
    )

    parser.add_argument(
        "--chroma-path",
        type=Path,
        default=DEFAULT_CHROMA_PATH,
        help=f"Output ChromaDB directory (default: {DEFAULT_CHROMA_PATH})"
    )

    # ── Database configuration ────────────────────────────────────
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help=f"ChromaDB collection name (default: {DEFAULT_COLLECTION_NAME})"
    )

    # ── Chunking parameters ───────────────────────────────────────
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help=f"Target chunk size in characters (default: {DEFAULT_CHUNK_SIZE})"
    )

    parser.add_argument(
        "--chunk-overlap",
        type=int,
        default=DEFAULT_CHUNK_OVERLAP,
        help=f"Overlap between chunks in characters (default: {DEFAULT_CHUNK_OVERLAP})"
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # ══════════════════════════════════════════════════════════════
    # Validate all inputs before processing
    # ══════════════════════════════════════════════════════════════

    # Check that PDF directory exists
    if not args.pdf_dir.exists():
        logger.error(f"PDF directory does not exist: {args.pdf_dir}")
        return

    # Check that PDF path is actually a directory (not a file)
    if not args.pdf_dir.is_dir():
        logger.error(f"PDF path is not a directory: {args.pdf_dir}")
        return

    # Ensure chunk size is reasonable (min 100 chars to be meaningful)
    if args.chunk_size < 100:
        logger.error("Chunk size must be at least 100 characters")
        return

    # Overlap must be smaller than chunk size (otherwise infinite loop)
    if args.chunk_overlap >= args.chunk_size:
        logger.error("Chunk overlap must be less than chunk size")
        return

    # ══════════════════════════════════════════════════════════════
    # All validation passed - run the indexing process
    # ══════════════════════════════════════════════════════════════
    index_pdfs(
        pdf_dir=args.pdf_dir,
        chroma_path=args.chroma_path,
        collection_name=args.collection,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )


if __name__ == "__main__":
    main()
