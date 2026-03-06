"""
Obsidian Plugin HTTP Bridge

HTTP API for Obsidian plugins to sync semantic tags to PostgreSQL.
Runs on localhost:5555 to bridge the Electron sandbox gap.

Endpoints:
  POST /tags/sync      - Sync tags from a note
  GET  /tags/<file>    - Get tags for a file
  POST /tags/batch     - Batch sync multiple notes
  GET  /concepts       - List all concepts
  GET  /health         - Health check
"""

import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import json

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow Obsidian to call from Electron

# Database config - will be injected
DB_CONFIG = {
    'host': '192.168.1.177',
    'port': 2665,
    'database': 'kj',
    'user': 'postgres',
    'password': 'Moss9pep28$'
}


def get_db_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def init_tables():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Semantic tags table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS obsidian_tags (
                    id SERIAL PRIMARY KEY,
                    uuid VARCHAR(36) UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    tag_type VARCHAR(50) NOT NULL,
                    label TEXT NOT NULL,
                    parent_uuid VARCHAR(36),
                    custom_type VARCHAR(100),
                    metadata JSONB DEFAULT '{}',
                    line_number INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_tags_file ON obsidian_tags(file_path);
                CREATE INDEX IF NOT EXISTS idx_tags_type ON obsidian_tags(tag_type);
                CREATE INDEX IF NOT EXISTS idx_tags_label ON obsidian_tags(label);
            """)
            
            # Concepts index table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS obsidian_concepts (
                    id SERIAL PRIMARY KEY,
                    label TEXT NOT NULL,
                    normalized_label TEXT NOT NULL UNIQUE,
                    total_count INTEGER DEFAULT 1,
                    file_count INTEGER DEFAULT 1,
                    tag_types TEXT[] DEFAULT '{}',
                    related_concepts TEXT[] DEFAULT '{}',
                    first_seen_file TEXT,
                    first_seen_date TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_concepts_norm ON obsidian_concepts(normalized_label);
            """)
            
            # Cross-document relations
            cur.execute("""
                CREATE TABLE IF NOT EXISTS obsidian_relations (
                    id SERIAL PRIMARY KEY,
                    source_file TEXT NOT NULL,
                    target_file TEXT NOT NULL,
                    shared_concepts TEXT[] DEFAULT '{}',
                    relationship_strength FLOAT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    UNIQUE(source_file, target_file)
                );
            """)
            
            conn.commit()
            logger.info("Database tables initialized")
    finally:
        conn.close()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        return jsonify({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500


@app.route('/tags/sync', methods=['POST'])
def sync_tags():
    """
    Sync tags from a single note.
    
    Body: {
        "filePath": "path/to/note.md",
        "tags": [
            {
                "uuid": "...",
                "type": "Axiom",
                "label": "...",
                "parentUuid": null,
                "customType": null,
                "metadata": {},
                "lineNumber": 10
            }
        ]
    }
    """
    data = request.json
    file_path = data.get('filePath')
    tags = data.get('tags', [])
    
    if not file_path:
        return jsonify({'error': 'filePath required'}), 400
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Clear existing tags for this file
            cur.execute("DELETE FROM obsidian_tags WHERE file_path = %s", (file_path,))
            
            # Insert new tags
            for tag in tags:
                cur.execute("""
                    INSERT INTO obsidian_tags 
                    (uuid, file_path, tag_type, label, parent_uuid, custom_type, metadata, line_number)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (uuid) DO UPDATE SET
                        file_path = EXCLUDED.file_path,
                        tag_type = EXCLUDED.tag_type,
                        label = EXCLUDED.label,
                        parent_uuid = EXCLUDED.parent_uuid,
                        custom_type = EXCLUDED.custom_type,
                        metadata = EXCLUDED.metadata,
                        line_number = EXCLUDED.line_number,
                        updated_at = NOW()
                """, (
                    tag.get('uuid'),
                    file_path,
                    tag.get('type'),
                    tag.get('label'),
                    tag.get('parentUuid'),
                    tag.get('customType'),
                    json.dumps(tag.get('metadata', {})),
                    tag.get('lineNumber')
                ))
            
            conn.commit()
            
        return jsonify({
            'success': True,
            'file': file_path,
            'tagCount': len(tags)
        })
    except Exception as e:
        conn.rollback()
        logger.error(f"Error syncing tags: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/tags/<path:file_path>', methods=['GET'])
def get_tags(file_path):
    """Get all tags for a file."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT uuid, tag_type as type, label, parent_uuid as "parentUuid",
                       custom_type as "customType", metadata, line_number as "lineNumber"
                FROM obsidian_tags 
                WHERE file_path = %s
                ORDER BY line_number
            """, (file_path,))
            tags = cur.fetchall()
            
        return jsonify({'file': file_path, 'tags': tags})
    finally:
        conn.close()


@app.route('/tags/batch', methods=['POST'])
def batch_sync():
    """Batch sync multiple notes."""
    data = request.json
    notes = data.get('notes', [])
    
    results = []
    conn = get_db_connection()
    try:
        for note in notes:
            file_path = note.get('filePath')
            tags = note.get('tags', [])
            
            with conn.cursor() as cur:
                cur.execute("DELETE FROM obsidian_tags WHERE file_path = %s", (file_path,))
                
                for tag in tags:
                    cur.execute("""
                        INSERT INTO obsidian_tags 
                        (uuid, file_path, tag_type, label, parent_uuid, custom_type, metadata, line_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (uuid) DO UPDATE SET
                            file_path = EXCLUDED.file_path,
                            tag_type = EXCLUDED.tag_type,
                            label = EXCLUDED.label,
                            updated_at = NOW()
                    """, (
                        tag.get('uuid'),
                        file_path,
                        tag.get('type'),
                        tag.get('label'),
                        tag.get('parentUuid'),
                        tag.get('customType'),
                        json.dumps(tag.get('metadata', {})),
                        tag.get('lineNumber')
                    ))
                
            results.append({'file': file_path, 'tagCount': len(tags), 'success': True})
        
        conn.commit()
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        conn.rollback()
        logger.error(f"Batch sync error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()



@app.route('/concepts', methods=['GET'])
def list_concepts():
    """List all indexed concepts."""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT label, normalized_label, total_count, file_count, 
                       tag_types, related_concepts
                FROM obsidian_concepts
                ORDER BY total_count DESC
                LIMIT %s OFFSET %s
            """, (limit, offset))
            concepts = cur.fetchall()
            
        return jsonify({'concepts': concepts})
    finally:
        conn.close()


@app.route('/concepts/rebuild', methods=['POST'])
def rebuild_concepts():
    """Rebuild concept index from tags."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM obsidian_concepts")
            
            cur.execute("""
                INSERT INTO obsidian_concepts (label, normalized_label, total_count, file_count, tag_types, first_seen_file)
                SELECT 
                    MAX(label) as label,
                    LOWER(TRIM(label)) as normalized_label,
                    COUNT(*) as total_count,
                    COUNT(DISTINCT file_path) as file_count,
                    ARRAY_AGG(DISTINCT tag_type) as tag_types,
                    MIN(file_path) as first_seen_file
                FROM obsidian_tags
                GROUP BY LOWER(TRIM(label))
                ON CONFLICT (normalized_label) DO UPDATE SET
                    total_count = EXCLUDED.total_count,
                    file_count = EXCLUDED.file_count,
                    tag_types = EXCLUDED.tag_types,
                    updated_at = NOW()
            """)
            
            conn.commit()
            cur.execute("SELECT COUNT(*) as count FROM obsidian_concepts")
            result = cur.fetchone()
            
        return jsonify({'success': True, 'conceptCount': result['count']})
    except Exception as e:
        conn.rollback()
        logger.error(f"Rebuild error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/stats', methods=['GET'])
def get_stats():
    """Get index statistics."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as tag_count FROM obsidian_tags")
            tag_count = cur.fetchone()['tag_count']
            
            cur.execute("SELECT COUNT(DISTINCT file_path) as file_count FROM obsidian_tags")
            file_count = cur.fetchone()['file_count']
            
            cur.execute("SELECT COUNT(*) as concept_count FROM obsidian_concepts")
            concept_count = cur.fetchone()['concept_count']
            
            cur.execute("""
                SELECT tag_type, COUNT(*) as count 
                FROM obsidian_tags 
                GROUP BY tag_type 
                ORDER BY count DESC
            """)
            type_breakdown = {row['tag_type']: row['count'] for row in cur.fetchall()}
            
        return jsonify({
            'totalTags': tag_count,
            'totalFiles': file_count,
            'totalConcepts': concept_count,
            'typeBreakdown': type_breakdown
        })
    finally:
        conn.close()


def run_bridge(host='127.0.0.1', port=5555, debug=False):
    """Run the HTTP bridge server."""
    init_tables()
    logger.info(f"Starting Obsidian bridge on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_bridge(debug=True)
