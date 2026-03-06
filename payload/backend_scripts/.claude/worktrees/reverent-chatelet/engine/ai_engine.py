# engine/ai_engine.py

"""
Full AI Engine with:
- OpenAI/Anthropic integration
- Vector embeddings
- Semantic search
- Definition generation
- Ontology building
- Tag/category inference
"""

from typing import List, Dict, Any, Optional, Tuple
import sqlite3
import numpy as np
from pathlib import Path
import json
import requests


class AIEngine:
    """
    AI Engine supporting:
    - OpenAI GPT-4/Claude for text generation
    - Text embeddings for semantic search
    - Definition auto-completion
    - Ontology inference
    - Citation and concept extraction
    """
    
    def __init__(self, settings, db_engine=None):
        self.settings = settings
        self.db = db_engine
        self.model_name = settings.model_name or "gpt-4o"
        
        # Try to import AI libraries
        self.openai_available = self._check_openai()
        self.anthropic_available = self._check_anthropic()
        
        # Initialize embedding cache
        self.embedding_cache: Dict[str, List[float]] = {}
        
        # Check Ollama availability
        self.ollama_available = self._check_ollama()
        self.ollama_model = "llama3.2"  # Default model, can be changed
    
    def _check_openai(self) -> bool:
        """Check if OpenAI library is available."""
        try:
            import openai
            self.openai = openai
            # Check if API key is set
            import os
            return bool(os.getenv("OPENAI_API_KEY"))
        except ImportError:
            return False
    
    def _check_anthropic(self) -> bool:
        """Check if Anthropic library is available."""
        try:
            import anthropic
            self.anthropic = anthropic
            import os
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            return False
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def list_ollama_models(self) -> List[str]:
        """List available Ollama models."""
        if not self.ollama_available:
            return []
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except:
            pass
        return []
    
    def generate_with_ollama(self, prompt: str, model: str = None) -> str:
        """
        Generate text using local Ollama instance.
        Great for YAML generation and quick tasks without API costs.
        """
        if not self.ollama_available:
            return "(Ollama not available - is it running?)"
        
        model = model or self.ollama_model
        
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            if response.status_code == 200:
                return response.json().get("response", "")
            else:
                return f"(Ollama error: {response.status_code})"
        except Exception as e:
            return f"(Ollama error: {e})"
    
    def generate_yaml_frontmatter(self, note_content: str, note_type: str = "auto") -> str:
        """
        Use Ollama to auto-generate YAML frontmatter for a note.
        This is the key integration for automatic YAML generation.
        
        Args:
            note_content: The content of the note
            note_type: Hint for type (stage/axiom/theorem/definition/claim/evidence/auto)
        
        Returns:
            YAML frontmatter string (without --- delimiters)
        """
        type_hint = "" if note_type == "auto" else f"The note type should be: {note_type}"
        
        prompt = f"""You are a YAML frontmatter generator for an academic Theophysics framework.
Analyze the note content and generate appropriate YAML frontmatter.

Rules:
- Return ONLY valid YAML, no markdown code blocks, no explanation
- Generate a UUID in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
- Identify the type: stage, axiom, theorem, definition, claim, evidence, or note
- Extract relevant tags from content
- Identify domains: physics, theology, information-theory, consciousness, mathematics
- Set status to: draft

{type_hint}

Note content:
{note_content[:1500]}

YAML frontmatter:"""

        result = self.generate_with_ollama(prompt)
        
        # Clean up response
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
        if result.startswith("yaml"):
            result = result[4:].strip()
        
        return result
    
    def classify_semantic_content(self, text: str) -> Dict[str, Any]:
        """
        Use Ollama to classify content for semantic tagging.
        Returns classifications matching the SEMANTIC MARKUP PROTOCOL.
        """
        prompt = f"""Classify this text for a Theophysics knowledge base.
Return a JSON object with "classifications" array.

Categories to use:
- Foundational: terms, axioms, theorem, postulate
- Evidence: claims, evidence, hypothesis
- Argumentation: objection, response, synthesis
- Connections: relationship, bridge, implication
- Framework: dark (paradox), light (resolved), trinity (3-part pattern)
- Math: equation, variable, law

Text:
{text[:1000]}

Return ONLY valid JSON:"""

        result = self.generate_with_ollama(prompt)
        
        try:
            # Clean and parse JSON
            result = result.strip()
            if result.startswith("```"):
                result = result.split("```")[1]
                if result.startswith("json"):
                    result = result[4:]
            return json.loads(result)
        except:
            return {"classifications": []}
    
    def is_available(self) -> Dict[str, bool]:
        """Check which AI services are available."""
        return {
            "openai": self.openai_available,
            "anthropic": self.anthropic_available,
            "ollama": self.ollama_available,
            "any": self.openai_available or self.anthropic_available or self.ollama_available
        }

    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding vector for a single text.
        Uses OpenAI text-embedding-3-small by default.
        """
        if use_cache and text in self.embedding_cache:
            return self.embedding_cache[text]
        
        if not self.openai_available:
            # Return dummy embedding if OpenAI not available
            import hashlib
            # Generate consistent dummy vector based on text hash
            hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
            np.random.seed(hash_val % (2**32))
            vector = np.random.randn(1536).tolist()  # Match OpenAI dimensions
            return vector
        
        try:
            response = self.openai.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            vector = response.data[0].embedding
            
            if use_cache:
                self.embedding_cache[text] = vector
            
            return vector
        except Exception as e:
            print(f"Embedding error: {e}")
            return [0.0] * 1536  # Return zero vector on error

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Batch embed multiple texts.
        """
        return [self.embed_text(text) for text in texts]

    def generate_definition(self, term: str, context: str = "") -> str:
        """
        AI-assisted definition generation.
        Uses GPT-4 or Claude to generate a definition given context.
        """
        if not self.openai_available and not self.anthropic_available:
            return f"(AI not available) Please define {term} manually."
        
        prompt = f"""Generate a concise, accurate definition for the term: "{term}"

Context from notes:
{context}

Provide a definition that is:
1. Clear and precise
2. Academically rigorous
3. 2-3 sentences
4. Includes key characteristics

Definition:"""

        try:
            if self.openai_available and "gpt" in self.model_name.lower():
                response = self.openai.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
            
            elif self.anthropic_available:
                client = self.anthropic.Anthropic()
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()
            
        except Exception as e:
            return f"(Error generating definition: {e})"
        
        return f"(AI not configured) Please define {term} manually."

    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Semantic search across all notes using embeddings.
        Returns top-k most similar notes.
        """
        if not self.db:
            return []
        
        # Get query embedding
        query_vector = np.array(self.embed_text(query))
        
        # Get all notes with their content
        conn = sqlite3.connect(self.db.db_path)
        c = conn.cursor()
        c.execute("SELECT path, title, yaml FROM notes")
        notes = c.fetchall()
        conn.close()
        
        # Calculate similarities
        similarities = []
        for path, title, yaml_str in notes:
            try:
                # Read note content
                note_text = Path(path).read_text(encoding="utf-8", errors="ignore")
                # Truncate to first 1000 chars for embedding
                note_text = note_text[:1000]
                
                # Get embedding
                note_vector = np.array(self.embed_text(note_text))
                
                # Calculate cosine similarity
                similarity = np.dot(query_vector, note_vector) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(note_vector)
                )
                
                similarities.append({
                    "path": path,
                    "title": title,
                    "similarity": float(similarity)
                })
            except Exception:
                continue
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]

    def infer_classification(self, definition_text: str) -> str:
        """
        Use AI to infer the classification/type of a definition.
        Returns: concept, theorem, principle, entity, process, etc.
        """
        if not self.openai_available:
            # Simple keyword-based fallback
            text_lower = definition_text.lower()
            if "theorem" in text_lower:
                return "theorem"
            elif "principle" in text_lower or "law" in text_lower:
                return "principle"
            elif "process" in text_lower or "method" in text_lower:
                return "process"
            elif "person" in text_lower or "born" in text_lower:
                return "entity-person"
            else:
                return "concept"
        
        prompt = f"""Classify this definition into ONE category:
- concept: abstract idea or notion
- theorem: mathematical or logical theorem
- principle: fundamental truth or law
- process: method or procedure
- entity-person: historical figure or person
- entity-place: location or institution
- term: technical terminology

Definition: {definition_text[:300]}

Category (one word):"""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for speed
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content.strip().lower()
        except Exception:
            return "concept"

    def extract_related_concepts(self, text: str, max_concepts: int = 10) -> List[str]:
        """
        Use AI to extract key related concepts from text.
        """
        if not self.openai_available:
            # Simple extraction: capitalized phrases
            import re
            concepts = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
            return list(set(concepts))[:max_concepts]
        
        prompt = f"""Extract the {max_concepts} most important concepts, terms, or ideas from this text.
Return ONLY a comma-separated list.

Text: {text[:500]}

Concepts:"""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.3
            )
            concepts_str = response.choices[0].message.content.strip()
            concepts = [c.strip() for c in concepts_str.split(',')]
            return concepts[:max_concepts]
        except Exception:
            return []

    def build_ontology_connections(self, term: str, definition: str) -> Dict[str, List[str]]:
        """
        Use AI to infer ontology connections for a term.
        Returns: parent_concepts, child_concepts, related_concepts
        """
        if not self.openai_available:
            return {
                "parent_concepts": [],
                "child_concepts": [],
                "related_concepts": []
            }
        
        prompt = f"""Given this term and definition, identify:
1. Parent concepts (broader categories it belongs to)
2. Child concepts (more specific instances or types)
3. Related concepts (similar or connected ideas)

Term: {term}
Definition: {definition[:300]}

Format your response as:
Parents: concept1, concept2
Children: concept3, concept4
Related: concept5, concept6

Response:"""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            text = response.choices[0].message.content.strip()
            
            # Parse response
            parents = []
            children = []
            related = []
            
            for line in text.split('\n'):
                if line.startswith('Parents:'):
                    parents = [c.strip() for c in line.replace('Parents:', '').split(',')]
                elif line.startswith('Children:'):
                    children = [c.strip() for c in line.replace('Children:', '').split(',')]
                elif line.startswith('Related:'):
                    related = [c.strip() for c in line.replace('Related:', '').split(',')]
            
            return {
                "parent_concepts": [p for p in parents if p],
                "child_concepts": [c for c in children if c],
                "related_concepts": [r for r in related if r]
            }
        except Exception:
            return {
                "parent_concepts": [],
                "child_concepts": [],
                "related_concepts": []
            }

    def summarize_note(self, note_path: Path, max_length: int = 200) -> str:
        """
        Generate an AI summary of a note.
        """
        if not note_path.exists():
            return ""
        
        text = note_path.read_text(encoding="utf-8", errors="ignore")
        
        if not self.openai_available:
            # Simple extractive summary: first few sentences
            sentences = text.split('.')[:3]
            return '. '.join(sentences) + '.'
        
        prompt = f"""Summarize this note in {max_length} words or less. Focus on the key ideas and concepts.

Note:
{text[:2000]}

Summary:"""

        try:
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"(Summary error: {e})"

    def get_ai_status(self) -> Dict[str, Any]:
        """Get status of AI services."""
        status = {
            "openai_available": self.openai_available,
            "anthropic_available": self.anthropic_available,
            "ollama_available": self.ollama_available,
            "model_name": self.model_name,
            "ollama_model": self.ollama_model if self.ollama_available else None,
            "embedding_cache_size": len(self.embedding_cache),
        }
        
        if self.openai_available:
            import os
            status["openai_key_set"] = bool(os.getenv("OPENAI_API_KEY"))
        
        if self.anthropic_available:
            import os
            status["anthropic_key_set"] = bool(os.getenv("ANTHROPIC_API_KEY"))
        
        if self.ollama_available:
            status["ollama_models"] = self.list_ollama_models()
        
        return status

