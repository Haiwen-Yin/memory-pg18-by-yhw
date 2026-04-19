# memory-pg18-by-yhw - AI Agent Memory System (PostgreSQL 18 + Apache AGE)

## Overview

A production-ready, platform-agnostic AI Agent memory system built on PostgreSQL 18 with pgvector and Apache AGE Property Graph integration. This skill provides a complete toolkit for implementing hybrid semantic search and graph-based relationship traversal in AI applications.

**Version**: v0.2.0  
**Author**: Haiwen Yin (胖头鱼 🐟)  
**License**: Apache License 2.0  
**Last Updated**: 2026-04-19 CST

---

## 🎯 **What This Skill Does**

This skill enables you to:
1. Deploy a memory system with PostgreSQL 18 on any platform (Docker, bare metal, cloud)
2. Store AI knowledge as vectors (semantic embeddings) and concepts (graph nodes)
3. Perform hybrid search combining vector similarity + graph relationship traversal
4. Query relationships using Cypher for multi-hop reasoning
5. Scale to millions of records with HNSW indexing

---

## 📦 **Package Contents**

```
memory-pg18-by-yhw-v0.2.0/
├── README.md                    # Full project documentation (English)
├── LICENSE                      # Apache License 2.0 full text
├── NOTICE                       # Third-party attributions and legal notices
├── VERSION                      # Version identifier (v0.2.0)
├── .gitignore                   # Git ignore rules for this project
├── docs/
│   └── deployment-guide.md      # Detailed deployment instructions for various platforms
├── scripts/
│   └── init_memory_system.sql  # Complete database schema and setup SQL
└── examples/
    ├── basic_usage.py           # Python SDK example with BGE-M3 embeddings
    └── sample_data.sql          # Sample INSERT statements for testing
```

---

## 🏗️ **Architecture**

### Hybrid Memory Model (Vector + Graph)

This skill implements a dual-layer memory architecture:

1. **Semantic Layer (pgvector)**: 
   - Stores concept embeddings as `VECTOR(1024)` columns
   - Uses HNSW indexing for fast approximate nearest neighbor search
   - Enables cosine similarity matching for semantic queries

2. **Relationship Layer (Apache AGE)**:
   - Models concepts as graph nodes with properties
   - Defines relationships using Cypher query language
   - Supports multi-hop traversal for reasoning chains

### Why Hybrid?

Pure vector search lacks explicit relationship modeling, while pure graph search struggles with fuzzy matching and semantic understanding. This hybrid approach gives you the best of both worlds:

- **Semantic retrieval**: Find similar concepts even without exact name matches
- **Relationship reasoning**: Traverse connected knowledge for multi-hop queries
- **Flexibility**: Use either layer independently or combine them in complex queries

---

## 🚀 **Usage Guide**

### 1. Quick Deployment (Docker)

```bash
# Pull and start PostgreSQL 18 with extensions
docker run -d --name pg-memory \
  -e POSTGRES_PASSWORD=your_password \
  -p 5432:5432 \
  postgres:18-alpine

# Install required extensions
docker exec -it pg-memory psql -U postgres << 'EOSQL'
CREATE EXTENSION vector;
CREATE EXTENSION age;
CREATE DATABASE memory_graph;
EOSQL

# Connect and initialize
docker exec -it pg-memory psql -U postgres -d memory_graph \
  -f /path/to/memory-pg18-by-yhw/scripts/init_memory_system.sql
```

### 2. Python Integration (SDK)

See `examples/basic_usage.py` for complete examples:

```python
from flagembedding import EmbeddingModel
import psycopg2
import numpy as np

# Initialize embedding model (BGE-M3, 1024 dimensions)
model = EmbeddingModel("BAAI/bge-m3")

# Generate embedding for your text
text = "Your knowledge content here"
embedding = model.encode([text])[0].tolist()

# Store in database with concept metadata
cursor.execute("""
    INSERT INTO memory.concepts (name, category, description, embedding)
    VALUES (%s, %s, %s, %s::vector)
""", ("Concept Name", "category_type", "Description text", embedding))
```

### 3. Semantic Search Query

```python
# Find top-5 most similar concepts to a query vector
cursor.execute("""
    SELECT name, category, 
           1 - (embedding <=> %s::vector) as similarity_score
    FROM memory.concepts
    ORDER BY similarity_score DESC
    LIMIT 5;
""", (query_embedding,))
```

### 4. Graph Relationship Query (Cypher)

```python
# Find all relationships connected to a concept
cursor.execute("""
    SELECT * FROM cypher('memory_graph', $$
        MATCH (c:concepts {name: 'Concept Name'})-[:RELATION_TYPE]->(related:concepts)
        RETURN c.name, type(rel), related.name, rel.strength
    $$) AS (start_node agtype, relation_type agtype, end_node agtype, strength float);
""")
```

---

## 🔧 **Configuration Options**

### Vector Embedding Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Dimension Size | 1024 | BGE-M3 embedding size (adjustable) |
| Similarity Metric | Cosine | `vector_cosine_ops` for cosine distance |
| HNSW m | 16 | Links per node in graph structure |
| HNSW ef_construction | 200 | Index building quality vs speed tradeoff |

### Graph Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| Label Type | `concepts` | Node label for concept entities |
| Relation Types | Dynamic | Define custom relationship types per domain |
| Strength Range | 0.0 - 1.0 | Float weight for edges (default: 1.0) |

---

## 📈 **Performance Optimization**

### Indexing Strategies

1. **HNSW Index**: Always create on `embedding` column for semantic search
   ```sql
   CREATE INDEX idx_concepts_embedding 
   ON memory.concepts USING hnsw (embedding vector_cosine_ops) 
   WITH (m = 16, ef_construction = 200);
   ```

2. **B-tree Index**: For category filtering
   ```sql
   CREATE INDEX idx_concepts_category ON memory.concepts(category);
   ```

3. **Foreign Key Constraints**: Ensure referential integrity for relations table
   ```sql
   ALTER TABLE memory.relations 
   ADD CONSTRAINT fk_from_concept FOREIGN KEY (from_concept_id) REFERENCES memory.concepts(concept_id);
   ALTER TABLE memory.relations 
   ADD CONSTRAINT fk_to_concept FOREIGN KEY (to_concept_id) REFERENCES memory.concepts(concept_id);
   ```

### Query Optimization Tips

- **Filter by category first**, then apply vector search:
  ```sql
  SELECT * FROM memory.concepts 
  WHERE category = 'user_profile' 
    AND embedding IS NOT NULL
  ORDER BY embedding <=> %s::vector LIMIT 5;
  ```

- **Use EXPLAIN ANALYZE** to identify bottlenecks:
  ```bash
  psql -d memory_graph << 'EOSQL'
  EXPLAIN ANALYZE 
  SELECT * FROM memory.concepts 
  ORDER BY embedding <=> '[0.1,0.2,...]'::vector LIMIT 5;
  EOSQL
  ```

---

## 🧪 **Testing & Validation**

### Basic Sanity Check

```bash
# Verify schema creation
psql -U postgres -d memory_graph << 'EOSQL'
SELECT table_name FROM information_schema.tables WHERE table_schema = 'memory';
-- Expected output: concepts, relations
EOSQL

# Test vector insertion and retrieval
psql -U postgres -d memory_graph << 'EOSQL'
INSERT INTO memory.concepts (name, category, description, embedding) 
VALUES ('test', 'testing', 'Sanity check', ARRAY[0.1, 0.2, ...]);  -- 1024 dims

SELECT name FROM memory.concepts WHERE name = 'test';
-- Expected output: test
EOSQL
```

### Performance Benchmark Script

See `scripts/benchmark.py` (not included in v0.2.0 but available on request):

- Insert 1K sample records
- Measure HNSW index build time
- Time semantic search queries (<30ms target)
- Test multi-hop traversal latency (<100ms for 3 hops)

---

## 🐛 **Troubleshooting**

### Common Issues & Solutions

#### Issue 1: PostgreSQL fails to start after extension installation

**Symptoms**: `FATAL:  could not load library ".../vector.so": file too short`  
**Cause**: Extension binary incompatible with PG version or corrupted copy  

**Solution**:
```bash
# Recompile pgvector from source on target host
git clone https://github.com/pgvector/pgvector.git
cd pgvector && make && sudo make install

# Verify control file compatibility (PG 18 specific)
cat /usr/local/pgsql/share/extension/vector.control
# Remove "microversion_format" parameter if present
```

#### Issue 2: Cypher queries return empty results unexpectedly

**Symptoms**: `SELECT * FROM cypher(...) AS (...)` returns no rows despite data existing  

**Cause**: Data inserted via SQL but not visible to AGE graph layer  
**Solution**: Ensure you're using the correct database name in Cypher context:
```sql
-- Correct usage - specify memory_graph as first argument
SELECT * FROM cypher('memory_graph', $$ ... $$) AS (...);

-- Incorrect - missing database specification
SELECT * FROM cypher($$ ... $$) AS (...);  -- This won't work!
```

#### Issue 3: Vector dimension mismatch errors

**Symptoms**: `error: vector dimensions do not match`  

**Solution**: Ensure all vectors are exactly 1024 dimensions for BGE-M3:
```python
embedding = model.encode([text])[0]  # Should be shape (1024,)
assert len(embedding) == 1024, f"Expected 1024 dims, got {len(embedding)}"
```

---

## 📚 **Related Skills**

- `oracle-memory-by-yhw`: Oracle AI Database version of this memory system (v0.1.0)
- `memory-pg18-by-yhw`: This PostgreSQL 18 + Apache AGE implementation (v0.2.0)
- `planning-with-files`: Manus-style file-based planning for complex tasks

---

## 📄 **License & Attribution**

This project is licensed under **Apache License 2.0**. See LICENSE file for full terms.

For third-party component attributions and legal notices, see NOTICE file.

---

## 👤 **Author & Contributors**

- **Original Author**: Haiwen Yin (胖头鱼 🐟) - Oracle/PostgreSQL/MySQL ACE Database Expert
- **Blog**: https://blog.csdn.net/yhw1809
- **GitHub**: https://github.com/Haiwen-Yin
- **Location**: Xipu Town, Pidu District, Chengdu, Sichuan, China

---

## 🔄 **Version History**

| Version | Date | Changes |
|---------|------|---------|
| v0.2.0 | 2026-04-19 | Initial release with Apache AGE Property Graph support, Apache License 2.0 migration |
| v0.1.0 | N/A | Previous Oracle AI Database version (separate skill) |

---

## 📞 **Support & Contact**

For issues, feature requests, or collaboration:
- Open an issue on GitHub: https://github.com/Haiwen-Yin/memory-pg18-by-yhw/issues
- Email: Available via blog contact form
- WeChat: Search "胖头鱼" (available for Chinese speakers)

---

## 🎓 **Educational Resources**

To understand the underlying technologies better:

1. **Apache AGE Tutorial**: https://age.apache.org/age-site/v1.7/docs/tutorial.html
2. **pgvector Quick Start**: https://github.com/pgvector/pgvector#quick-start
3. **Cypher Query Language Manual**: https://neo4j.com/docs/cypher-manual/current/
4. **HNSW Algorithm Explained**: https://arxiv.org/abs/1603.09320 (original paper)

---

**Ready to deploy!** 🚀  
For complete deployment instructions, see `docs/deployment-guide.md`.
