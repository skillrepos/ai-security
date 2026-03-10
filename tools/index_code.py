#!/usr/bin/env python3
"""
index_code.py
────────────────────────────────────────────────────────────────────
Create a **fresh** ChromaDB vector-index from source code files using
intelligent chunking, language detection, and rich metadata for optimal
code search and RAG performance.

High-level flow
---------------
1. **Reset DB** – delete any existing code database for a clean start.
2. **Scan codebase** – recursively find code files (Python, JS/TS, Java, Go, etc.)
3. **Language-aware chunking** – split code respecting language structure and
   token limits while preserving complete logical units.
4. **Metadata extraction** – capture file path, language, line numbers, and context.
5. **Embed** – convert each chunk to a 384-dimensional vector (MiniLM-L6-v2).
6. **Store** – write `(vector, code, metadata)` into a persistent Chroma
   collection called `"code_index"`.

Best Practices
--------------
- **Multi-language support**: Python, JavaScript/TypeScript, Java, Go, Rust,
  C/C++, Ruby, PHP, C#, and more
- **Semantic chunking**: Respects blank lines and logical boundaries
- **Token-aware**: Uses tiktoken to prevent chunks from exceeding context limits
- **Rich metadata**: Language, file path, line numbers, file size for filtering
- **Separate database**: Uses ./chroma_code_db to avoid mixing with PDF vectors

Usage
-----
python index_code.py [--code-dir PATH] [--chroma-path PATH] [--max-tokens N]

Arguments:
  --code-dir      Root directory to scan recursively (default: ../ - project root)
  --chroma-path   Output ChromaDB directory (default: ./chroma_code_db)
  --max-tokens    Maximum tokens per chunk (default: 500)
  --collection    ChromaDB collection name (default: code_index)
"""

# ───────────────────── standard-library imports ────────────────────
import argparse
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Iterable
import logging

# ───────────────────── 3rd-party imports ───────────────────────────
# All imports have graceful error handling with installation instructions

try:
    # SentenceTransformer converts code to vector embeddings
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("ERROR: sentence-transformers not installed. Install with: pip install sentence-transformers")
    exit(1)

try:
    # tiktoken counts tokens to prevent exceeding context limits
    from tiktoken import encoding_for_model
except ImportError:
    print("ERROR: tiktoken not installed. Install with: pip install tiktoken")
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

# Default directory to scan (one level up from tools/ to get project root)
DEFAULT_CODE_DIR = Path("../")

# Default output directory for ChromaDB (separate from PDF database)
DEFAULT_CHROMA_PATH = Path("./chroma_code_db")

# Default collection name (different from PDF collection)
DEFAULT_COLLECTION_NAME = "code_index"

# Embedding model from HuggingFace
# all-MiniLM-L6-v2: Fast, 384-dim vectors, good balance of speed and quality
# Same model as PDFs to keep embeddings in same semantic space
DEFAULT_EMBED_MODEL = "all-MiniLM-L6-v2"

# Maximum tokens per chunk (keeps chunks within LLM context limits)
# 500 tokens ≈ 1-2 functions or 20-50 lines of code
DEFAULT_MAX_TOKENS = 500

# Directories to skip during recursive scanning
# These are build artifacts, dependencies, or version control metadata
# Skipping these dramatically improves indexing speed and prevents polluting
# the index with third-party code that isn't part of the project
SKIP_DIRS = {
    ".git", ".hg", ".svn",                    # Version control metadata
    "__pycache__", ".pytest_cache",           # Python bytecode cache
    "node_modules", ".npm",                   # Node.js dependencies (can be huge!)
    ".venv", "venv", "env", "py_env",         # Python virtual environments
    "site-packages", "dist-packages",         # Python installed packages
    "build", "dist", "target",                # Build outputs (compiled artifacts)
    ".next", ".nuxt", ".output",              # JavaScript framework build folders
    "vendor", "Pods",                         # Ruby/iOS dependencies
    ".idea", ".vscode", ".vs",                # IDE configuration files
    "coverage", ".nyc_output",                # Test coverage reports
}

# Supported code file extensions mapped to language names
# This enables language-specific metadata and potential future language-aware processing
# Extensions are mapped to normalized language names for consistent metadata
CODE_EXTENSIONS = {
    # Python
    ".py": "python",
    ".pyw": "python",
    ".pyi": "python",

    # JavaScript/TypeScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mjs": "javascript",
    ".cjs": "javascript",

    # Web
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",

    # Java/JVM
    ".java": "java",
    ".kt": "kotlin",
    ".scala": "scala",
    ".groovy": "groovy",

    # C/C++
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hh": "cpp",
    ".hxx": "cpp",

    # C#/.NET
    ".cs": "csharp",
    ".fs": "fsharp",
    ".vb": "visualbasic",

    # Go
    ".go": "go",

    # Rust
    ".rs": "rust",

    # Ruby
    ".rb": "ruby",
    ".rake": "ruby",

    # PHP
    ".php": "php",
    ".phtml": "php",

    # Swift/Objective-C
    ".swift": "swift",
    ".m": "objective-c",

    # Shell scripts
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "zsh",

    # Other
    ".sql": "sql",
    ".r": "r",
    ".R": "r",
    ".lua": "lua",
    ".vim": "vim",
    ".el": "elisp",
}

# ╔════════════════════════════════════════════════════════════════╗
# 2.  Code chunking with language awareness                        ║
# ╚════════════════════════════════════════════════════════════════╝

def chunk_code(code: str, max_tokens: int = DEFAULT_MAX_TOKENS,
               language: str = "generic") -> Iterable[Dict[str, Any]]:
    """
    Yield code chunks that respect language structure and token limits.

    This function splits code into semantically meaningful chunks without
    breaking lines or logical units (like functions). It uses blank lines
    as natural boundaries and tracks line numbers for precise references.

    Strategy
    --------
    1. Count tokens for each line using tiktoken (GPT-3.5 tokenizer)
    2. Accumulate lines until:
       - Adding the next line would exceed max_tokens, OR
       - We hit a blank line (natural boundary between logical sections)
    3. Track start/end line numbers for each chunk (enables source linking)
    4. Never split a line of code mid-line (preserves syntax)

    Parameters
    ----------
    code : str
        The source code to chunk.
    max_tokens : int
        Maximum tokens per chunk.
    language : str
        Programming language (for future language-specific logic).

    Yields
    ------
    Dict[str, Any]
        Each chunk with 'text', 'start_line', 'end_line' fields.
    """
    # Initialize tokenizer for GPT-3.5 (good proxy for context limits)
    # tiktoken provides accurate token counts that match OpenAI's models
    enc = encoding_for_model("gpt-3.5-turbo")

    # State variables for building chunks
    current_lines: List[str] = []  # Lines being accumulated for current chunk
    token_count = 0                # Running token count for current chunk
    start_line = 1                 # Line number where current chunk starts (1-indexed)
    current_line = 1               # Current line number being processed

    # Process the code line by line
    # We never split a line mid-line to preserve syntax validity
    for line in code.splitlines():
        # Count tokens for this line (including the newline character)
        # The +"\n" ensures we account for the newline in the token count
        line_tokens = len(enc.encode(line + "\n"))

        # ─────────────────────────────────────────────────────────────
        # HARD BREAK: Next line would exceed token budget
        # ─────────────────────────────────────────────────────────────
        # If adding this line would push us over max_tokens, we must
        # yield the current chunk and start a new one
        if current_lines and token_count + line_tokens > max_tokens:
            # Yield the accumulated chunk with line number metadata
            yield {
                "text": "\n".join(current_lines),  # Reconstruct multi-line text
                "start_line": start_line,          # First line of chunk
                "end_line": current_line - 1,      # Last line of chunk
                "token_count": token_count         # Actual token count
            }
            # Reset state for next chunk
            current_lines, token_count = [], 0
            start_line = current_line  # New chunk starts at current line

        # ─────────────────────────────────────────────────────────────
        # SOFT BREAK: Blank line signals logical boundary
        # ─────────────────────────────────────────────────────────────
        # Blank lines often separate functions, classes, or logical blocks
        # This creates more semantically meaningful chunks
        if not line.strip() and current_lines:
            # Yield the chunk (only if we have accumulated content)
            yield {
                "text": "\n".join(current_lines),
                "start_line": start_line,
                "end_line": current_line - 1,
                "token_count": token_count
            }
            # Reset for next chunk
            # Note: We skip the blank line itself to avoid empty chunks
            current_lines, token_count = [], 0
            start_line = current_line + 1
            current_line += 1
            continue  # Skip adding the blank line to the next chunk

        # Add this line to the current chunk being built
        current_lines.append(line)
        token_count += line_tokens
        current_line += 1

    # Don't forget to yield the final chunk
    # The file might not end with a blank line or exceed token limit
    if current_lines:
        yield {
            "text": "\n".join(current_lines),
            "start_line": start_line,
            "end_line": current_line - 1,
            "token_count": token_count
        }


def should_index_file(file_path: Path) -> bool:
    """
    Determine if a file should be indexed based on extension and name.

    This filters out non-source files to avoid indexing dependencies,
    lock files, and other non-code content.

    Parameters
    ----------
    file_path : Path
        Path to the file to check.

    Returns
    -------
    bool
        True if file should be indexed, False otherwise.
    """
    # Check if extension is in our supported list of code file types
    # For example, .py, .js, .java, etc.
    if file_path.suffix.lower() not in CODE_EXTENSIONS:
        return False

    # Skip hidden files (those starting with a dot)
    # These are typically config files like .gitignore, .env
    if file_path.name.startswith("."):
        return False

    # Skip common dependency lock files and package manifests
    # These are large, not source code, and would pollute the index
    skip_files = {
        "package-lock.json", "yarn.lock", "Gemfile.lock",
        "poetry.lock", "Pipfile.lock", "requirements.txt"
    }
    if file_path.name.lower() in skip_files:
        return False

    return True


def get_language(file_path: Path) -> str:
    """
    Detect programming language from file extension.

    Uses the CODE_EXTENSIONS mapping to identify the language.
    Returns "unknown" for unsupported extensions.

    Parameters
    ----------
    file_path : Path
        Path to the source file.

    Returns
    -------
    str
        Language name (e.g., 'python', 'javascript', 'java').
    """
    # Look up the extension in our mapping (case-insensitive)
    # Returns "unknown" if the extension isn't in our supported list
    return CODE_EXTENSIONS.get(file_path.suffix.lower(), "unknown")


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

def index_codebase(code_dir: Path, chroma_path: Path, collection_name: str,
                   max_tokens: int) -> None:
    """
    Index all code files in the specified directory into ChromaDB.

    Parameters
    ----------
    code_dir : Path
        Root directory to scan recursively.
    chroma_path : Path
        Output directory for ChromaDB.
    collection_name : str
        Name of the ChromaDB collection.
    max_tokens : int
        Maximum tokens per chunk.
    """
    # ══════════════════════════════════════════════════════════════
    # SETUP PHASE: Initialize all components before processing
    # ══════════════════════════════════════════════════════════════

    # ── 1. Validate directory ─────────────────────────────────────
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir.resolve()}")
        return

    if not code_dir.is_dir():
        logger.error(f"Code path is not a directory: {code_dir.resolve()}")
        return

    logger.info(f"Scanning codebase from: {code_dir.resolve()}")

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
        collection = client.get_or_create_collection(collection_name)
        logger.info(f"Created collection: {collection_name}")
    except Exception as e:
        logger.error(f"Failed to create ChromaDB client: {e}")
        return

    # ══════════════════════════════════════════════════════════════
    # INDEXING PHASE: Scan and process all code files
    # ══════════════════════════════════════════════════════════════

    # Initialize statistics counters for final summary report
    file_counter = 0                        # Total files successfully indexed
    chunk_counter = 0                       # Total code chunks created
    language_stats: Dict[str, int] = {}     # Count files per language

    # ── 5. Recursively scan for code files ────────────────────────
    # os.walk() traverses the directory tree depth-first
    for root, dirs, files in os.walk(code_dir):
        # In-place filter to prevent os.walk() from descending into skip folders
        # The [:] slice assignment modifies the list in-place, which tells
        # os.walk() to skip those directories entirely (not just ignore files in them)
        # This dramatically speeds up scanning and avoids indexing dependencies
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_DIRS and not d.startswith(".")
        ]

        # Process each file in the current directory
        for name in files:
            file_path = Path(root) / name

            # ═══════════════════════════════════════════════════════════
            # STEP A: Filter non-code files
            # ═══════════════════════════════════════════════════════════
            # Skip files that aren't source code (lock files, hidden files, etc.)
            if not should_index_file(file_path):
                continue

            # ═══════════════════════════════════════════════════════════
            # STEP B: Detect language and read file
            # ═══════════════════════════════════════════════════════════
            # Determine programming language from file extension
            language = get_language(file_path)

            # Read the file contents
            try:
                # Use UTF-8 encoding with error tolerance
                # errors="ignore" prevents crashes on files with encoding issues
                code_text = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as err:
                logger.warning(f"Could not read {file_path}: {err}")
                continue

            # Skip empty files (no point indexing nothing)
            if not code_text.strip():
                continue

            # Get file size in bytes for metadata
            # This enables filtering by file size in queries
            try:
                file_size = file_path.stat().st_size
            except:
                file_size = 0  # If we can't get size, default to 0

            # ═══════════════════════════════════════════════════════════
            # STEP C: Chunk the code into logical units
            # ═══════════════════════════════════════════════════════════
            # Split the file into token-limited chunks with line tracking
            chunks = list(chunk_code(code_text, max_tokens, language))

            # Skip files that produced no chunks (shouldn't happen but be safe)
            if not chunks:
                continue

            # ═══════════════════════════════════════════════════════════
            # STEP D: Embed and store each chunk
            # ═══════════════════════════════════════════════════════════
            # Process chunks in batches to balance memory usage and performance
            # Batching reduces API/model overhead while keeping memory reasonable
            batch_size = 50  # 50 chunks at a time works well for most files

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]  # Get next batch of chunks

                # Extract just the text content for embedding
                # The chunks dict also contains line numbers, token counts, etc.
                texts = [chunk["text"] for chunk in batch]

                # ─────────────────────────────────────────────────────
                # Generate vector embeddings for this batch
                # ─────────────────────────────────────────────────────
                # SentenceTransformer converts each code snippet into a 384-dim vector
                try:
                    embeddings = embed_model.encode(texts, show_progress_bar=False)
                    # Convert numpy arrays to lists for ChromaDB compatibility
                    embeddings_list = [emb.tolist() for emb in embeddings]
                except Exception as e:
                    logger.error(f"Failed to generate embeddings for {file_path}: {e}")
                    continue  # Skip this batch but try others

                # ─────────────────────────────────────────────────────
                # Create unique IDs for each chunk
                # ─────────────────────────────────────────────────────
                # Format: "relative/path/file.py:10-25" (path with line range)
                # This makes it easy to link back to the exact source location
                rel_path = file_path.relative_to(code_dir)
                ids = [
                    f"{rel_path}:{chunk['start_line']}-{chunk['end_line']}"
                    for chunk in batch
                ]

                # ─────────────────────────────────────────────────────
                # Build metadata for each chunk
                # ─────────────────────────────────────────────────────
                # Rich metadata enables powerful filtering and citation in RAG queries
                metadatas = [
                    {
                        "file_path": str(rel_path),        # Relative path from project root
                        "language": language,               # Programming language
                        "start_line": chunk["start_line"],  # First line of chunk (for linking)
                        "end_line": chunk["end_line"],      # Last line of chunk (for linking)
                        "chunk_index": i + j,               # Order within this file
                        "total_chunks": len(chunks),        # Total chunks in this file
                        "file_size": file_size,             # File size in bytes (for filtering)
                        "extension": file_path.suffix,      # File extension (e.g., ".py")
                    }
                    for j, chunk in enumerate(batch)
                ]

                # ─────────────────────────────────────────────────────
                # Store everything in ChromaDB
                # ─────────────────────────────────────────────────────
                # Each entry has: unique ID, vector embedding, original code, and metadata
                try:
                    collection.add(
                        ids=ids,                    # Unique identifier with line numbers
                        embeddings=embeddings_list, # 384-dim vectors for similarity search
                        documents=texts,            # Original code for retrieval
                        metadatas=metadatas        # Language, path, lines, etc.
                    )
                except Exception as e:
                    logger.error(f"Failed to add chunks to ChromaDB: {e}")
                    continue  # Try next batch

            # Update running statistics for final summary report
            file_counter += 1
            chunk_counter += len(chunks)
            language_stats[language] = language_stats.get(language, 0) + 1

            # Log progress (helps user know it's working on large codebases)
            logger.info(f"Indexed {rel_path} ({language}): {len(chunks)} chunks")

    # ══════════════════════════════════════════════════════════════
    # SUMMARY: Report indexing results
    # ══════════════════════════════════════════════════════════════
    # Provide a clear summary of what was indexed
    logger.info(f"\n{'='*60}")
    logger.info(f"Indexing complete!")
    logger.info(f"  Total files indexed: {file_counter}")
    logger.info(f"  Total code chunks: {chunk_counter}")
    logger.info(f"  Database location: {chroma_path.resolve()}")
    logger.info(f"  Collection name: {collection_name}")

    # Show breakdown by programming language (helps verify expected files were indexed)
    if language_stats:
        logger.info(f"\n  Files by language:")
        # Sort by count descending (most files first)
        for lang, count in sorted(language_stats.items(), key=lambda x: -x[1]):
            logger.info(f"    {lang}: {count} files")

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
        description="Index source code files into ChromaDB for RAG and code search.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default settings (scan from project root)
  python index_code.py

  # Specify custom code directory
  python index_code.py --code-dir /path/to/project

  # Customize chunk size
  python index_code.py --max-tokens 1000

  # Full customization
  python index_code.py --code-dir ./src --chroma-path ./my_code_db --max-tokens 750
        """
    )

    # ── Input/Output paths ────────────────────────────────────────
    # Configure where to scan for code and where to store the database
    parser.add_argument(
        "--code-dir",
        type=Path,
        default=DEFAULT_CODE_DIR,
        help=f"Root directory to scan recursively (default: {DEFAULT_CODE_DIR} - project root)"
    )

    parser.add_argument(
        "--chroma-path",
        type=Path,
        default=DEFAULT_CHROMA_PATH,
        help=f"Output ChromaDB directory (default: {DEFAULT_CHROMA_PATH})"
    )

    # ── Database configuration ────────────────────────────────────
    # Collection name for organizing code vectors (separate from PDF collection)
    parser.add_argument(
        "--collection",
        type=str,
        default=DEFAULT_COLLECTION_NAME,
        help=f"ChromaDB collection name (default: {DEFAULT_COLLECTION_NAME})"
    )

    # ── Chunking parameters ───────────────────────────────────────
    # Control how code is split into chunks for embedding
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=DEFAULT_MAX_TOKENS,
        help=f"Maximum tokens per chunk (default: {DEFAULT_MAX_TOKENS})"
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # ══════════════════════════════════════════════════════════════
    # Validate all inputs before processing
    # ══════════════════════════════════════════════════════════════

    # Resolve the code directory to absolute path for clarity
    # This eliminates any ambiguity from relative paths like "../"
    code_dir = args.code_dir.resolve()

    # Check that code directory exists
    if not code_dir.exists():
        logger.error(f"Code directory does not exist: {code_dir}")
        return

    # Check that code path is actually a directory (not a file)
    if not code_dir.is_dir():
        logger.error(f"Code path is not a directory: {code_dir}")
        return

    # Ensure max_tokens is reasonable (min 50 tokens to be meaningful)
    # Very small chunks would be fragmented and useless for RAG
    if args.max_tokens < 50:
        logger.error("Max tokens must be at least 50")
        return

    # ══════════════════════════════════════════════════════════════
    # All validation passed - run the indexing process
    # ══════════════════════════════════════════════════════════════
    # This will scan the codebase, chunk files, generate embeddings,
    # and store everything in ChromaDB with rich metadata
    index_codebase(
        code_dir=code_dir,              # Where to scan for code
        chroma_path=args.chroma_path,   # Where to store the database
        collection_name=args.collection, # Collection name in ChromaDB
        max_tokens=args.max_tokens      # Max tokens per chunk
    )


if __name__ == "__main__":
    main()
