-- ============================================
-- Sample Data for Memory System v0.2.0
-- Platform-agnostic AI Agent Knowledge Base
-- ============================================

BEGIN;

-- Clear existing data (for demo purposes)
DELETE FROM memory.relations;
DELETE FROM memory.concepts;

-- Insert sample concepts
INSERT INTO memory.concepts (concept_id, name, category, description, content) VALUES
    ('user-001', '胖头鱼 🐟', 'user_profile', 
     'Oracle/PostgreSQL/MySQL ACE 数据库专家，专注于 AI Agent Memory System 开发',
     '{"name": "胖头鱼", "nickname": "尹海文", "role": "ACE DB Expert"}'),
    
    ('db-001', 'Oracle AI Database 26ai', 'knowledge_base/database', 
     'Oracle AI Database Enterprise Edition (v23.26.1)',
     '{"version": "26ai", "features": ["DBMS_VECTOR_DATABASE"]}'),
     
    ('tech-001', 'Apache AGE', 'knowledge_base/technology', 
     'PostgreSQL Property Graph extension with Cypher support',
     '{"project": "apache.org", "license": "MIT", "version": "1.7.0"}');

-- Create relationships
INSERT INTO memory.relations (from_concept_id, to_concept_id, relation_type, strength) VALUES
    ((SELECT concept_id FROM memory.concepts WHERE name = '胖头鱼 🐟'),
     (SELECT concept_id FROM memory.concepts WHERE name = 'Oracle AI Database 26ai'),
     'RELATED_TO', 0.9),
    
    ((SELECT concept_id FROM memory.concepts WHERE name = 'Oracle AI Database 26ai'),
     (SELECT concept_id FROM memory.concepts WHERE name = 'Apache AGE'),
     'EXTENDS', 0.8);

COMMIT;

-- Verification query
SELECT 
    from_c.name || ' --[' || r.relation_type || ']--> ' || to_c.name as graph_path,
    r.strength as confidence
FROM memory.relations r
JOIN memory.concepts from_c ON r.from_concept_id = from_c.concept_id
JOIN memory.concepts to_c ON r.to_concept_id = to_c.concept_id;
