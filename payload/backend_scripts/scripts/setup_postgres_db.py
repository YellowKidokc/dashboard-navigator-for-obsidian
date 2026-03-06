"""
Setup PostgreSQL database for Theophysics
"""
import psycopg2

# Connection to postgres (default db) to create our database
conn_str = "host=192.168.1.177 port=2665 dbname=postgres user=Yellowkid password=Moss9pep28$"

try:
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Check if database exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'Theophysics'")
    if cur.fetchone():
        print("Database 'Theophysics' already exists")
    else:
        cur.execute('CREATE DATABASE "Theophysics"')
        print("Database 'Theophysics' created!")
    
    conn.close()
    
    # Now connect to the new database and create tables
    conn = psycopg2.connect("host=192.168.1.177 port=2665 dbname=Theophysics user=Yellowkid password=Moss9pep28$")
    cur = conn.cursor()
    
    # Create semantic_tags table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS semantic_tags (
        id SERIAL PRIMARY KEY,
        uuid TEXT UNIQUE NOT NULL,
        axis TEXT NOT NULL,
        value TEXT NOT NULL,
        note_path TEXT NOT NULL,
        note_uuid TEXT,
        created_at INTEGER,
        updated_at INTEGER,
        UNIQUE(axis, value, note_path)
    )
    """)
    
    # Create tagged_notes table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tagged_notes (
        id SERIAL PRIMARY KEY,
        uuid TEXT UNIQUE NOT NULL,
        path TEXT UNIQUE NOT NULL,
        title TEXT,
        epistemic_tag TEXT,
        function_tags JSONB,
        domain_tags JSONB,
        path_tag TEXT,
        is_complete INTEGER DEFAULT 0,
        created_at INTEGER,
        updated_at INTEGER
    )
    """)
    
    # Create tag_stats table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tag_stats (
        id SERIAL PRIMARY KEY,
        uuid TEXT UNIQUE NOT NULL,
        axis TEXT NOT NULL,
        value TEXT NOT NULL,
        usage_count INTEGER DEFAULT 0,
        last_used_at INTEGER,
        UNIQUE(axis, value)
    )
    """)
    
    conn.commit()
    print("Tables created successfully!")
    
    # Verify
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchall()
    print(f"Tables in database: {[t[0] for t in tables]}")
    
    conn.close()
    print("\nPostgreSQL setup complete!")
    print("Connection string: host=192.168.1.177 port=2665 dbname=Theophysics user=Yellowkid")
    
except Exception as e:
    print(f"Error: {e}")
