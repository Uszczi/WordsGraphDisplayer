import os
import re
from pathlib import Path
from typing import Dict, List, Set
from collections import defaultdict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Relation(BaseModel):
    """Represents a relation between two words"""
    rel_type: str  # e.g., "appears_with"
    connect_to: str  # the word this word connects to


class Node(BaseModel):
    """Represents a word node with its relations"""
    id: str  # the word itself
    value: str  # display value (same as id, could be enhanced)
    node_type: str = "word"  # "word" or "director"
    relations: List[Relation]
    original_lines: List[str] = []  # original lines where this word appeared


class APIResponse(BaseModel):
    """API response wrapper"""
    nodes: List[Node]
    total_count: int


# ============================================================================
# DATA LOADER
# ============================================================================

class FilmsGraphBuilder:
    """Builds a word graph from Films YYYY.md files"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path).expanduser()
        self.word_relations: Dict[str, Set[str]] = defaultdict(set)
        self.word_lines: Dict[str, List[str]] = defaultdict(list)  # track original lines
        self.word_types: Dict[str, str] = {}  # track node type (word or director)
        self.original_case: Dict[str, str] = {}  # preserve original case for directors
        self.all_words: Set[str] = set()

    def load_films_files(self) -> None:
        """Load all Films YYYY.md files matching pattern Films20[0-9]+"""
        pattern = re.compile(r"Films\s*20\d{2}\.md")

        if not self.storage_path.exists():
            print(f"Warning: Storage path {self.storage_path} does not exist")
            return

        for file_path in self.storage_path.glob("*.md"):
            if pattern.match(file_path.name):
                self._parse_file(file_path)

    def _parse_file(self, file_path: Path) -> None:
        """Parse a single Films file and extract words/relations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split by lines, each line is typically: "Title (Year) **Director**"
            lines = content.strip().split('\n')
            for line in lines:
                if line.strip():
                    self._extract_words_from_line(line)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")

    def _extract_words_from_line(self, line: str) -> None:
        """
        Extract words from a line and create relations.
        Handles directors separately (inside **) without splitting by comma.
        """
        original_line = line.strip()
        
        # Extract title and directors separately
        # Pattern: Title (Year) **Director1, Director2, ...**
        bold_pattern = r'\*\*(.+?)\*\*'
        bold_match = re.search(bold_pattern, line)
        
        directors_text = ""
        title_text = line
        
        if bold_match:
            directors_text = bold_match.group(1)
            title_text = re.sub(bold_pattern, '', line)
        
        # Remove common words that might not be meaningful
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'are', 'was', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'can', 'vs'
        }
        
        # Extract title words
        title_words = re.findall(r'[a-zA-Z]+', title_text.lower())
        meaningful_title_words = [w for w in title_words if w not in stop_words and len(w) > 2]
        
        # Extract and process directors (split by comma, but don't split names within)
        meaningful_directors = []
        if directors_text:
            directors_list = [d.strip() for d in directors_text.split(',')]
            for director in directors_list:
                director_name = director.strip()  # Keep original case
                director_name_lower = director_name.lower()  # For comparison
                if director_name_lower and len(director_name_lower) > 2:
                    # Store director with original case but use lowercase as key
                    if director_name_lower not in self.all_words:
                        self.all_words.add(director_name_lower)
                        # Store the original case version
                        self.original_case[director_name_lower] = director_name
                    
                    self.word_types[director_name_lower] = "director"
                    meaningful_directors.append(director_name_lower)
                    
                    # Track original line for director
                    if original_line not in self.word_lines[director_name_lower]:
                        self.word_lines[director_name_lower].append(original_line)
        
        # Add title words to our set
        self.all_words.update(meaningful_title_words)
        for word in meaningful_title_words:
            self.word_types[word] = "word"
        
        # Track original line for title words
        for word in meaningful_title_words:
            if original_line not in self.word_lines[word]:
                self.word_lines[word].append(original_line)
        
        # Create relations between consecutive title words
        for i in range(len(meaningful_title_words) - 1):
            word1 = meaningful_title_words[i]
            word2 = meaningful_title_words[i + 1]
            
            if word1 != word2:
                self.word_relations[word1].add(word2)
                self.word_relations[word2].add(word1)
        
        # Create relations between title words and directors
        for title_word in meaningful_title_words:
            for director in meaningful_directors:
                if title_word != director:
                    self.word_relations[title_word].add(director)
                    self.word_relations[director].add(title_word)

    def build_nodes(self) -> List[Node]:
        """Build Node objects from extracted word relations"""
        nodes = []

        for word in sorted(self.all_words):
            relations = [
                Relation(rel_type="appears_with", connect_to=related_word)
                for related_word in sorted(self.word_relations[word])
            ]

            # Use original case for directors, lowercase for regular words
            display_value = self.original_case.get(word, word)
            
            node = Node(
                id=word,
                value=display_value,
                node_type=self.word_types.get(word, "word"),
                relations=relations,
                original_lines=self.word_lines[word]
            )
            nodes.append(node)

        return nodes


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Words Graph Displayer",
        description="API to display word graphs from Films metadata"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins (change to specific domains in production)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Load data at startup
    storage_path = os.getenv("STORAGE_PATH", "~/Documents/zetel/Zettelkasten/")
    builder = FilmsGraphBuilder(storage_path)
    builder.load_films_files()
    nodes = builder.build_nodes()

    # Create lookup indices
    nodes_by_id = {node.id: node for node in nodes}

    @app.get("/api/nodes", response_model=APIResponse)
    async def get_all_nodes():
        """Get all word nodes and their relations"""
        return APIResponse(
            nodes=nodes,
            total_count=len(nodes)
        )

    @app.get("/api/nodes/{node_id}", response_model=Node)
    async def get_node(node_id: str):
        """Get a specific node by ID"""
        node_id = node_id.lower()
        if node_id not in nodes_by_id:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
        return nodes_by_id[node_id]

    @app.get("/api/stats")
    async def get_stats():
        """Get statistics about the graph"""
        total_relations = sum(len(node.relations) for node in nodes)
        avg_relations = total_relations / len(nodes) if nodes else 0

        return {
            "total_nodes": len(nodes),
            "total_relations": total_relations,
            "avg_relations_per_node": round(avg_relations, 2)
        }

    @app.get("/")
    async def root():
        """Root endpoint with API information"""
        return {
            "name": "Words Graph Displayer",
            "version": "1.0.0",
            "endpoints": {
                "GET /api/nodes": "Get all word nodes",
                "GET /api/nodes/{node_id}": "Get specific node",
                "GET /api/stats": "Get graph statistics"
            }
        }

    return app


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    app = create_app()
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
