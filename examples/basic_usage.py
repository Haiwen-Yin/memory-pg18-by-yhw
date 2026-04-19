#!/usr/bin/env python3
"""
Basic Usage Examples for memory-pg18-by-yhw v0.2.0
=====================================================

This script demonstrates how to use the Memory System with PostgreSQL 18 + Apache AGE.
Platform-agnostic: works with any AI Agent framework.

Requirements:
    - psycopg2-binary or pg8000
"""

import os
import json
from typing import Optional, List, Dict, Any
import psycopg2


class MemorySystem:
    """Platform-agnostic AI Agent Memory System"""
    
    def __init__(self, db_url: str = "postgresql://postgres:postgres@localhost:5432/memory_graph"):
        """Initialize connection to PostgreSQL database
        
        Args:
            db_url: Database connection string
        """
        self.conn = psycopg2.connect(db_url)
    
    def add_concept(
        self, 
        name: str, 
        category: str = 'custom',
        description: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None
    ) -> str:
        """Add a new concept to memory
        
        Args:
            name: Concept identifier/name
            category: Category for filtering
            description: Human-readable description
            content: JSON metadata (optional)
            embedding: Pre-computed embedding vector (optional)
            
        Returns:
            UUID of the created concept
        """
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT memory.add_concept(%s, %s, %s, %s::jsonb, %s::vector)
            """, (name, category, description or '', json.dumps(content) if content else '{}', embedding))
            
            concept_id = cur.fetchone()[0]
            self.conn.commit()
            return str(concept_id)
    
    def add_relation(
        self, 
        from_concept: str, 
        to_concept: str, 
        relation_type: str = 'related_to',
        strength: float = 1.0
    ) -> bool:
        """Create a relationship between two concepts
        
        Args:
            from_concept: UUID or name of source concept
            to_concept: UUID or name of target concept
            relation_type: Type of relationship (e.g., 'related_to', 'extends')
            strength: Relationship strength (0.0 - 1.0)
            
        Returns:
            True if successful
        """
        with self.conn.cursor() as cur:
            # Resolve names to UUIDs if needed
            concept_ids = []
            for name in [from_concept, to_concept]:
                cur.execute("SELECT concept_id FROM memory.concepts WHERE name = %s", (name,))
                result = cur.fetchone()
                if not result:
                    try:
                        uuid.UUID(name)
                        concept_ids.append(name)
                    except ValueError:
                        raise ValueError(f"Concept '{name}' not found")
                else:
                    concept_ids.append(str(result['concept_id']))
            
            cur.execute("""
                SELECT memory.add_relation(%s, %s, %s, %s)
            """, (concept_ids[0], concept_ids[1], relation_type, strength))
            
            self.conn.commit()
            return True
    
    def search_similar(
        self, 
        query_embedding: List[float],
        limit: int = 5, 
        min_score: float = 0.7,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Semantic search using vector similarity
        
        Args:
            query_embedding: Query embedding vector (pre-computed)
            limit: Maximum results to return
            min_score: Minimum similarity threshold (0.0 - 1.0)
            category_filter: Optional category filter
            
        Returns:
            List of matching concepts with scores
        """
        with self.conn.cursor() as cur:
            if category_filter:
                cur.execute("""
                    SELECT * FROM memory.search_similar(%s, %s, %s, %s)
                """, (query_embedding, limit, min_score, category_filter))
            else:
                cur.execute("""
                    SELECT * FROM memory.search_similar(%s, %s, %s, NULL)
                """, (query_embedding, limit, min_score))
            
            results = cur.fetchall()
            self.conn.commit()
            return [dict(row) for row in results]
    
    def close(self):
        """Close database connection"""
        self.conn.close()


# Example Usage
if __name__ == '__main__':
    # Initialize memory system
    memory = MemorySystem("postgresql://postgres:postgres@localhost:5432/memory_graph")
    
    try:
        # Add concepts
        user_id = memory.add_concept(
            name='胖头鱼 🐟',
            category='user_profile',
            description='Oracle/PostgreSQL/MySQL ACE 数据库专家',
            content={'name': '尹海文'}
        )
        
        oracle_id = memory.add_concept(
            name='Oracle AI Database',
            category='knowledge_base',
            description='Oracle AI Database Enterprise Edition v23.26.1'
        )
        
        # Create relationship
        memory.add_relation(user_id, oracle_id, 'RELATED_TO', 0.9)
        
        print("Memory system initialized successfully!")
        print(f"Created concepts: {user_id}, {oracle_id}")
        
    finally:
        memory.close()
