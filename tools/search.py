#!/usr/bin/env python3
"""
search.py
────────────────────────────────────────────────────────────────────
Search both code and PDF vector databases using semantic similarity.

This tool provides a unified interface for searching indexed content from
both source code (via index_code.py) and PDF documents (via index_pdfs.py).
It uses the same embedding model to ensure semantic consistency.

Features
--------
- **Multi-database support**: Search code or PDF collections
- **Semantic search**: Uses vector similarity, not keyword matching
- **Colorized output**: Best match highlighted, similarity scores shown
- **Rich metadata**: Shows source file, page/line numbers, language, etc.
- **Interactive mode**: REPL for multiple searches
- **CLI mode**: Single query via command-line arguments

Usage
-----
# Interactive mode (default: code search)
python search.py

# Interactive mode (PDF search)
python search.py --target pdfs

# Single query via CLI
python search.py --query "how to reset password" --target pdfs

# Customize number of results
python search.py --query "authentication function" --top-k 5 --target code

Arguments:
  --target      Which database to search: 'code' or 'pdfs' (default: code)
  --query       Search query (if not provided, enters interactive mode)
  --top-k       Number of results to return (default: 3)
  --chroma-path Path to ChromaDB directory (default: auto-detect based on target)
  --collection  Collection name (default: auto-detect based on target)
"""

# ───────────────────── standard-library imports ────────────────────
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# ───────────────────── 3rd-party imports ───────────────────────────
# All imports have graceful error handling

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy not installed. Install with: pip install numpy")
    sys.exit(1)

try:
    # SentenceTransformer for encoding queries (must match indexing model)
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
    sys.exit(1)

try:
    # ChromaDB for vector similarity search
    from chromadb import PersistentClient
    from chromadb.config import Settings, DEFAULT_TENANT, DEFAULT_DATABASE
except ImportError:
    print("ERROR: chromadb not installed. Install with: pip install chromadb")
    sys.exit(1)

# ───────────────────── logging setup ───────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ╔════════════════════════════════════════════════════════════════╗
# 1.  Configuration / constants                                    ║
# ╚════════════════════════════════════════════════════════════════╝

# Embedding model - MUST match the model used during indexing
# Using a different model will produce incompatible vectors
DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"

# Database paths and collection names for each target
# These must match the paths/collections used by the indexing scripts
DATABASE_CONFIGS = {
    "code": {
        "chroma_path": Path("./chroma_code_db"),
        "collection": "code_index",
        "description": "Source code repository"
    },
    "pdfs": {
        "chroma_path": Path("./chroma_db"),
        "collection": "pdf_documents",
        "description": "PDF documentation"
    }
}

# ANSI color codes for terminal output
# These work on most POSIX terminals (Linux, macOS, WSL)
COLORS = {
    "green": "\033[92m",   # Best match highlight
    "blue": "\033[94m",    # Other matches
    "yellow": "\033[93m",  # Metadata labels
    "red": "\033[91m",     # Similarity scores
    "cyan": "\033[96m",    # Headers
    "reset": "\033[0m",    # Reset to default
    "bold": "\033[1m",     # Bold text
}

# ╔════════════════════════════════════════════════════════════════╗
# 2.  Similarity calculation                                       ║
# ╚════════════════════════════════════════════════════════════════╝

def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.

    Cosine similarity measures the angle between vectors, ranging from
    -1 (opposite) to 1 (identical). For embeddings, values closer to 1
    indicate more similar semantic meaning.

    Parameters
    ----------
    vec_a : np.ndarray
        First vector (e.g., query embedding).
    vec_b : np.ndarray
        Second vector (e.g., document embedding).

    Returns
    -------
    float
        Cosine similarity score between -1 and 1.
    """
    # Compute dot product and magnitudes
    # The 1e-10 prevents division by zero for zero vectors
    dot_product = np.dot(vec_a, vec_b)
    magnitude_a = np.linalg.norm(vec_a)
    magnitude_b = np.linalg.norm(vec_b)

    return float(dot_product / (magnitude_a * magnitude_b + 1e-10))


# ╔════════════════════════════════════════════════════════════════╗
# 3.  Result formatting and display                                ║
# ╚════════════════════════════════════════════════════════════════╝

def format_code_metadata(metadata: Dict[str, Any]) -> str:
    """
    Format metadata for a code search result.

    Code results include file path, language, line numbers, etc.

    Parameters
    ----------
    metadata : Dict[str, Any]
        Metadata dictionary from the code index.

    Returns
    -------
    str
        Formatted metadata string for display.
    """
    # Extract metadata fields (with defaults for missing fields)
    file_path = metadata.get("file_path", "unknown")
    language = metadata.get("language", "unknown")
    start_line = metadata.get("start_line", "?")
    end_line = metadata.get("end_line", "?")
    chunk_index = metadata.get("chunk_index", "?")
    total_chunks = metadata.get("total_chunks", "?")

    # Format as readable string with color
    return (
        f"{COLORS['yellow']}Source:{COLORS['reset']} {file_path}\n"
        f"{COLORS['yellow']}Language:{COLORS['reset']} {language}\n"
        f"{COLORS['yellow']}Lines:{COLORS['reset']} {start_line}-{end_line}\n"
        f"{COLORS['yellow']}Chunk:{COLORS['reset']} {chunk_index + 1}/{total_chunks}"
    )


def format_pdf_metadata(metadata: Dict[str, Any]) -> str:
    """
    Format metadata for a PDF search result.

    PDF results include source document, page number, content type, etc.

    Parameters
    ----------
    metadata : Dict[str, Any]
        Metadata dictionary from the PDF index.

    Returns
    -------
    str
        Formatted metadata string for display.
    """
    # Extract metadata fields (with defaults for missing fields)
    source = metadata.get("source", "unknown")
    page = metadata.get("page", "?")
    content_type = metadata.get("type", "text")
    chunk_index = metadata.get("chunk_index", "?")
    total_chunks = metadata.get("total_chunks_on_page", "?")

    # Format as readable string with color
    result = (
        f"{COLORS['yellow']}Source:{COLORS['reset']} {source}\n"
        f"{COLORS['yellow']}Page:{COLORS['reset']} {page}\n"
        f"{COLORS['yellow']}Type:{COLORS['reset']} {content_type}"
    )

    # Add chunk info if available
    if chunk_index != "?" and total_chunks != "?":
        result += f"\n{COLORS['yellow']}Chunk:{COLORS['reset']} {chunk_index + 1}/{total_chunks}"

    return result


def display_results(query: str, documents: List[str], metadatas: List[Dict[str, Any]],
                   similarities: List[float], target: str) -> None:
    """
    Display search results in a formatted, colorized output.

    Results are numbered and separated with clear visual dividers.
    The best match (highest similarity) is highlighted in green.

    Parameters
    ----------
    query : str
        The original search query.
    documents : List[str]
        List of document text chunks.
    metadatas : List[Dict[str, Any]]
        List of metadata dictionaries for each result.
    similarities : List[float]
        List of similarity scores for each result.
    target : str
        Search target ('code' or 'pdfs') for metadata formatting.
    """
    # Print search header
    print(f"\n{COLORS['cyan']}{COLORS['bold']}{'='*80}{COLORS['reset']}")
    print(f"{COLORS['cyan']}{COLORS['bold']}Search Results for: \"{query}\"{COLORS['reset']}")
    print(f"{COLORS['cyan']}{COLORS['bold']}{'='*80}{COLORS['reset']}\n")

    # Find the best match (highest similarity score)
    best_idx = int(np.argmax(similarities))

    # Display each result
    for i, (doc, meta, sim) in enumerate(zip(documents, metadatas, similarities)):
        # Color the best match green, others blue
        result_color = COLORS['green'] if i == best_idx else COLORS['blue']

        # Result header with number
        separator = "-" * 80
        print(f"{result_color}{separator}")
        print(f"Result {i + 1}/{len(documents)}")
        print(f"{separator}{COLORS['reset']}\n")

        # Document content (truncate if very long)
        # This prevents overwhelming the terminal with huge chunks
        max_display_chars = 1000
        display_text = doc if len(doc) <= max_display_chars else doc[:max_display_chars] + "..."
        print(f"{display_text}\n")

        # Similarity score in red for emphasis
        print(f"{COLORS['red']}Similarity Score: {sim:.4f}{COLORS['reset']}\n")

        # Format metadata based on target type
        if target == "code":
            metadata_str = format_code_metadata(meta)
        else:  # pdfs
            metadata_str = format_pdf_metadata(meta)

        print(metadata_str)
        print()  # Blank line between results


# ╔════════════════════════════════════════════════════════════════╗
# 4.  Core search functionality                                    ║
# ╚════════════════════════════════════════════════════════════════╝

def search(query: str, target: str = "code", top_k: int = 3,
          chroma_path: Optional[Path] = None,
          collection_name: Optional[str] = None) -> None:
    """
    Search the vector database for semantically similar content.

    This function:
    1. Connects to the specified ChromaDB database
    2. Encodes the query using the same embedding model as indexing
    3. Performs vector similarity search
    4. Computes exact cosine similarities
    5. Displays results with formatting and metadata

    Parameters
    ----------
    query : str
        The search query (natural language).
    target : str
        Which database to search: 'code' or 'pdfs'.
    top_k : int
        Number of results to return (default: 3).
    chroma_path : Optional[Path]
        Path to ChromaDB directory (overrides default).
    collection_name : Optional[str]
        Collection name (overrides default).
    """
    # ══════════════════════════════════════════════════════════════
    # STEP 1: Validate target and get configuration
    # ══════════════════════════════════════════════════════════════
    if target not in DATABASE_CONFIGS:
        logger.error(f"Invalid target: {target}. Must be 'code' or 'pdfs'.")
        return

    # Get configuration for this target (use overrides if provided)
    config = DATABASE_CONFIGS[target]
    db_path = chroma_path or config["chroma_path"]
    collection = collection_name or config["collection"]

    # Validate database exists
    if not db_path.exists():
        logger.error(
            f"Database not found at {db_path.resolve()}\n"
            f"Run the appropriate indexing script first:\n"
            f"  - For code: python tools/index_code.py\n"
            f"  - For PDFs: python tools/index_pdfs.py"
        )
        return

    # ══════════════════════════════════════════════════════════════
    # STEP 2: Connect to ChromaDB and load collection
    # ══════════════════════════════════════════════════════════════
    try:
        # Connect to the persistent database on disk
        client = PersistentClient(
            path=str(db_path),
            settings=Settings(),
            tenant=DEFAULT_TENANT,
            database=DEFAULT_DATABASE,
        )

        # Get the collection (will error if it doesn't exist)
        coll = client.get_or_create_collection(name=collection)

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return

    # Check if collection has any content
    # An empty collection means nothing has been indexed yet
    try:
        collection_data = coll.get()
        total_chunks = len(collection_data.get("documents", []))
    except Exception as e:
        logger.error(f"Failed to read collection: {e}")
        return

    if total_chunks == 0:
        logger.warning(
            f"Collection '{collection}' is empty.\n"
            f"Run the indexing script first to populate the database."
        )
        return

    # Show collection statistics
    logger.info(f"Searching {config['description']}: {total_chunks} chunks indexed")

    # ══════════════════════════════════════════════════════════════
    # STEP 3: Load embedding model and encode query
    # ══════════════════════════════════════════════════════════════
    # Load the same model used during indexing to ensure compatibility
    try:
        embed_model = SentenceTransformer(DEFAULT_EMBED_MODEL)
    except Exception as e:
        logger.error(f"Failed to load embedding model: {e}")
        return

    # Convert query text to a 384-dimensional vector
    # This vector will be compared against all indexed content
    try:
        query_vector = embed_model.encode(query)
    except Exception as e:
        logger.error(f"Failed to encode query: {e}")
        return

    # ══════════════════════════════════════════════════════════════
    # STEP 4: Perform vector similarity search
    # ══════════════════════════════════════════════════════════════
    # ChromaDB finds the top_k most similar vectors using cosine distance
    try:
        results = coll.query(
            query_embeddings=[query_vector.tolist()],  # Convert numpy to list
            n_results=top_k,                            # How many results to return
            include=["documents", "metadatas", "embeddings"],  # What to include
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return

    # Extract results from ChromaDB response format
    # ChromaDB returns nested lists: [[result1, result2, ...]]
    documents = results["documents"][0]      # The actual text chunks
    metadatas = results["metadatas"][0]      # File paths, pages, languages, etc.
    embeddings = results["embeddings"][0]    # The 384-dim vectors

    # Handle case where no results were found
    if not documents:
        logger.warning("No matches found for your query.")
        return

    # ══════════════════════════════════════════════════════════════
    # STEP 5: Calculate exact cosine similarities
    # ══════════════════════════════════════════════════════════════
    # ChromaDB uses approximate search for speed, so we recalculate
    # exact similarities for more accurate scoring
    similarities = [
        cosine_similarity(query_vector, np.array(emb))
        for emb in embeddings
    ]

    # ══════════════════════════════════════════════════════════════
    # STEP 6: Display formatted results
    # ══════════════════════════════════════════════════════════════
    display_results(query, documents, metadatas, similarities, target)


# ╔════════════════════════════════════════════════════════════════╗
# 5.  Interactive REPL mode                                        ║
# ╚════════════════════════════════════════════════════════════════╝

def interactive_mode(target: str = "code", top_k: int = 3,
                    chroma_path: Optional[Path] = None,
                    collection_name: Optional[str] = None) -> None:
    """
    Run an interactive search REPL (Read-Eval-Print Loop).

    Users can enter multiple queries without restarting the program.
    The embedding model is loaded once and reused for all queries.

    Parameters
    ----------
    target : str
        Which database to search: 'code' or 'pdfs'.
    top_k : int
        Number of results per query.
    chroma_path : Optional[Path]
        Custom database path (overrides default).
    collection_name : Optional[str]
        Custom collection name (overrides default).
    """
    # Display welcome message with instructions
    config = DATABASE_CONFIGS.get(target, {})
    description = config.get("description", target)

    print(f"\n{COLORS['cyan']}{COLORS['bold']}{'='*80}{COLORS['reset']}")
    print(f"{COLORS['cyan']}{COLORS['bold']}Interactive Search - {description.title()}{COLORS['reset']}")
    print(f"{COLORS['cyan']}{COLORS['bold']}{'='*80}{COLORS['reset']}\n")
    print("Enter your search queries below.")
    print("Type 'exit', 'quit', or press Ctrl+C to exit.\n")

    # Main REPL loop
    while True:
        try:
            # Get user input
            # The prompt is blue to distinguish it from output
            user_input = input(f"{COLORS['blue']}Search: {COLORS['reset']}").strip()

            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "q"]:
                print(f"\n{COLORS['cyan']}Exiting search. Goodbye!{COLORS['reset']}\n")
                break

            # Skip empty queries
            if not user_input:
                print(f"{COLORS['yellow']}Please enter a search query.{COLORS['reset']}\n")
                continue

            # Perform the search
            search(user_input, target, top_k, chroma_path, collection_name)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print(f"\n\n{COLORS['cyan']}Interrupted. Exiting search.{COLORS['reset']}\n")
            break
        except Exception as e:
            # Catch any unexpected errors and continue
            logger.error(f"Error during search: {e}")
            print(f"{COLORS['red']}An error occurred. Please try again.{COLORS['reset']}\n")


# ╔════════════════════════════════════════════════════════════════╗
# 6.  CLI entry point                                              ║
# ╚════════════════════════════════════════════════════════════════╝

def main():
    """Parse command-line arguments and run search."""
    # ══════════════════════════════════════════════════════════════
    # Setup command-line argument parser
    # ══════════════════════════════════════════════════════════════
    parser = argparse.ArgumentParser(
        description="Search indexed code or PDF content using semantic similarity.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (code search)
  python search.py

  # Interactive mode (PDF search)
  python search.py --target pdfs

  # Single query via CLI
  python search.py --query "authentication logic" --target code

  # More results
  python search.py --query "password reset" --target pdfs --top-k 5

  # Custom database path
  python search.py --query "error handling" --chroma-path ./my_db
        """
    )

    # ── Search target ─────────────────────────────────────────────
    # Which database to search (code or PDFs)
    parser.add_argument(
        "--target",
        type=str,
        choices=["code", "pdfs"],
        default="code",
        help="Which database to search: 'code' or 'pdfs' (default: code)"
    )

    # ── Query parameters ──────────────────────────────────────────
    # Optional query for non-interactive mode
    parser.add_argument(
        "--query",
        type=str,
        help="Search query (if omitted, enters interactive mode)"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results to return (default: 3)"
    )

    # ── Database overrides ────────────────────────────────────────
    # Advanced options to override default paths
    parser.add_argument(
        "--chroma-path",
        type=Path,
        help="Path to ChromaDB directory (overrides default for target)"
    )

    parser.add_argument(
        "--collection",
        type=str,
        help="Collection name (overrides default for target)"
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # ══════════════════════════════════════════════════════════════
    # Validate inputs
    # ══════════════════════════════════════════════════════════════

    # Validate top_k is positive
    if args.top_k < 1:
        logger.error("--top-k must be at least 1")
        sys.exit(1)

    # ══════════════════════════════════════════════════════════════
    # Run search in appropriate mode
    # ══════════════════════════════════════════════════════════════

    if args.query:
        # ──────────────────────────────────────────────────────────
        # CLI mode: Single query, then exit
        # ──────────────────────────────────────────────────────────
        search(
            query=args.query,
            target=args.target,
            top_k=args.top_k,
            chroma_path=args.chroma_path,
            collection_name=args.collection
        )
    else:
        # ──────────────────────────────────────────────────────────
        # Interactive mode: REPL for multiple queries
        # ──────────────────────────────────────────────────────────
        interactive_mode(
            target=args.target,
            top_k=args.top_k,
            chroma_path=args.chroma_path,
            collection_name=args.collection
        )


if __name__ == "__main__":
    main()
