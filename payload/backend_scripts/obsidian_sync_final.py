"""
Obsidian to PostgreSQL Sync Tool - Final Version
Works with existing 'notes' table and adds versioning
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import psycopg2
from psycopg2.extras import Json
import os
from pathlib import Path
import hashlib
import json
from datetime import datetime
import threading
import re
import traceback
import yaml

class ObsidianSync:
    def __init__(self, root):
        self.root = root
        self.root.title("Obsidian → PostgreSQL Sync (Versioned)")
        self.root.geometry("1000x750")
        
        self.vault_path = tk.StringVar()
        self.db_host = tk.StringVar(value="192.168.1.177")
        self.db_port = tk.StringVar(value="2665")
        self.db_name = tk.StringVar(value="theophysics")
        self.db_user = tk.StringVar(value="Yellowkid")
        self.db_password = tk.StringVar()
        
        self.conn = None
        self.is_syncing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """Create the GUI layout"""
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title = ttk.Label(main_frame, text="Obsidian → PostgreSQL Sync", 
                         font=('Arial', 16, 'bold'))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        subtitle = ttk.Label(main_frame, text="With Versioning & Change Tracking", 
                            font=('Arial', 9), foreground='gray')
        subtitle.grid(row=1, column=0, columnspan=3, pady=(0, 15))
        
        # Vault Configuration
        vault_frame = ttk.LabelFrame(main_frame, text="Obsidian Vault", padding="10")
        vault_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        vault_frame.columnconfigure(1, weight=1)
        
        ttk.Label(vault_frame, text="Vault Path:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(vault_frame, textvariable=self.vault_path, width=50).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(vault_frame, text="Browse...", command=self.browse_vault).grid(row=0, column=2)
        
        # Database Configuration
        db_frame = ttk.LabelFrame(main_frame, text="PostgreSQL Database", padding="10")
        db_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        db_frame.columnconfigure(1, weight=1)
        
        ttk.Label(db_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(db_frame, textvariable=self.db_host).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        ttk.Label(db_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 5))
        ttk.Entry(db_frame, textvariable=self.db_port, width=10).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(db_frame, text="Database:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Entry(db_frame, textvariable=self.db_name).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=(5, 0))
        
        ttk.Label(db_frame, text="User:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Entry(db_frame, textvariable=self.db_user).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5, pady=(5, 0))
        
        ttk.Label(db_frame, text="Password:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=(5, 0))
        ttk.Entry(db_frame, textvariable=self.db_password, show="*").grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=(5, 0))
        
        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=(0, 10))
        
        self.test_btn = ttk.Button(button_frame, text="Test Connection", command=self.test_connection)
        self.test_btn.grid(row=0, column=0, padx=5)
        
        self.setup_btn = ttk.Button(button_frame, text="Setup Versioning", command=self.setup_versioning)
        self.setup_btn.grid(row=0, column=1, padx=5)
        
        self.sync_btn = ttk.Button(button_frame, text="Sync Notes", command=self.start_sync)
        self.sync_btn.grid(row=0, column=2, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", command=self.stop_sync, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=3, padx=5)
        
        ttk.Button(button_frame, text="View Stats", command=self.view_stats).grid(row=0, column=4, padx=5)
        
        # Progress
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Log Output
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Button(log_frame, text="Clear Log", command=self.clear_log).grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
        
    def log(self, message, level="INFO"):
        """Add message to log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        """Clear the log text"""
        self.log_text.delete(1.0, tk.END)
        
    def browse_vault(self):
        """Browse for Obsidian vault directory"""
        directory = filedialog.askdirectory(title="Select Obsidian Vault")
        if directory:
            self.vault_path.set(directory)
            self.log(f"Vault path set to: {directory}")
            
    def test_connection(self):
        """Test PostgreSQL connection"""
        self.log("Testing database connection...")
        try:
            conn = psycopg2.connect(
                host=self.db_host.get(),
                port=self.db_port.get(),
                database=self.db_name.get(),
                user=self.db_user.get(),
                password=self.db_password.get()
            )
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM notes")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            self.log(f"✓ Connection successful! Found {count} notes in database.", "SUCCESS")
            messagebox.showinfo("Success", f"Database connection successful!\n\nExisting notes: {count}")
        except Exception as e:
            self.log(f"✗ Connection failed: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Connection failed:\n{str(e)}")
    
    def setup_versioning(self):
        """Run the versioning setup SQL script"""
        self.log("Setting up versioning tables...")
        
        sql_file = Path(__file__).parent / "setup_versioning.sql"
        if not sql_file.exists():
            self.log("✗ setup_versioning.sql not found!", "ERROR")
            messagebox.showerror("Error", "setup_versioning.sql file not found in the same directory!")
            return
        
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_script = f.read()
            
            conn = psycopg2.connect(
                host=self.db_host.get(),
                port=self.db_port.get(),
                database=self.db_name.get(),
                user=self.db_user.get(),
                password=self.db_password.get()
            )
            cursor = conn.cursor()
            cursor.execute(sql_script)
            conn.commit()
            
            # Get table counts
            cursor.execute("""
                SELECT 
                    'notes' as table_name, COUNT(*) as row_count FROM notes
                UNION ALL
                SELECT 'note_versions', COUNT(*) FROM note_versions
                UNION ALL
                SELECT 'deleted_notes', COUNT(*) FROM deleted_notes
                ORDER BY table_name
            """)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            self.log("✓ Versioning setup complete!", "SUCCESS")
            for table, count in results:
                self.log(f"  {table}: {count} rows")
            
            messagebox.showinfo("Success", "Versioning tables created successfully!\n\nCheck the log for details.")
            
        except Exception as e:
            self.log(f"✗ Setup failed: {str(e)}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            messagebox.showerror("Error", f"Setup failed:\n{str(e)}")
    
    def safe_read_file(self, file_path):
        """Safely read file with multiple encoding attempts"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content, encoding, None
            except UnicodeDecodeError:
                continue
            except Exception as e:
                return None, None, str(e)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return content, 'utf-8-replace', "Used error replacement"
        except Exception as e:
            return None, None, str(e)
    
    def safe_parse_frontmatter(self, content):
        """Safely parse YAML frontmatter"""
        frontmatter = {}
        body = content
        errors = []
        
        if not content.startswith('---'):
            return frontmatter, body, errors
        
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                body = parts[2].strip()
                
                try:
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                    if not isinstance(frontmatter, dict):
                        frontmatter = {}
                        errors.append("YAML parsed but not a dict")
                except yaml.YAMLError as e:
                    errors.append(f"YAML parse error: {str(e)}")
                    for line in frontmatter_text.split('\n'):
                        if ':' in line:
                            try:
                                key, value = line.split(':', 1)
                                key = key.strip()
                                value = value.strip().strip('"\'')
                                
                                if value.startswith('[') and value.endswith(']'):
                                    value = [v.strip().strip('"\'') for v in value[1:-1].split(',') if v.strip()]
                                
                                frontmatter[key] = value
                            except:
                                continue
        except Exception as e:
            errors.append(f"Frontmatter extraction error: {str(e)}")
        
        return frontmatter, body, errors
    
    def extract_tags(self, content):
        """Extract tags from content"""
        tags = set()
        try:
            tag_pattern = r'#([a-zA-Z0-9_/-]+)'
            tags.update(re.findall(tag_pattern, content))
        except:
            pass
        return list(tags)
    
    def extract_links(self, content):
        """Extract wiki-style links"""
        links = set()
        try:
            link_pattern = r'\[\[([^\]]+)\]\]'
            matches = re.findall(link_pattern, content)
            for match in matches:
                try:
                    link = match.split('|')[0].strip()
                    links.add(link)
                except:
                    continue
        except:
            pass
        return list(links)
    
    def calculate_hash(self, content):
        """Calculate MD5 hash of content"""
        try:
            return hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()
        except:
            return hashlib.md5(str(content).encode('utf-8', errors='replace')).hexdigest()
    
    def get_file_timestamps(self, file_path):
        """Get file creation and modification timestamps"""
        try:
            stat = os.stat(file_path)
            return int(stat.st_ctime), int(stat.st_mtime)
        except:
            now = int(datetime.now().timestamp())
            return now, now
    
    def sync_note(self, file_path, cursor, vault_path):
        """Sync a single note with versioning"""
        errors = []
        
        try:
            content, encoding, read_error = self.safe_read_file(file_path)
            if content is None:
                error_msg = f"Failed to read file: {read_error}"
                cursor.execute("""
                    INSERT INTO sync_errors (file_path, error_type, error_message)
                    VALUES (%s, %s, %s)
                """, (str(file_path), "READ_ERROR", error_msg))
                return 'error', [error_msg]
            
            if read_error:
                errors.append(f"Encoding: {read_error}")
            
            frontmatter, body, fm_errors = self.safe_parse_frontmatter(content)
            errors.extend(fm_errors)
            
            title = frontmatter.get('title', Path(file_path).stem)
            note_type = frontmatter.get('type', 'note')
            tags = self.extract_tags(content)
            
            if 'tags' in frontmatter:
                fm_tags = frontmatter['tags']
                if isinstance(fm_tags, list):
                    tags.extend([str(t) for t in fm_tags])
                elif fm_tags:
                    tags.append(str(fm_tags))
            
            tags = list(set(tags))
            links = self.extract_links(content)
            file_hash = self.calculate_hash(content)
            word_count = len(content.split())
            created_at, modified_at = self.get_file_timestamps(file_path)
            
            rel_path = str(Path(file_path).relative_to(vault_path))
            folder = str(Path(rel_path).parent) if Path(rel_path).parent != Path('.') else ''
            
            yaml_str = json.dumps(frontmatter) if frontmatter else None
            tags_str = ','.join(tags) if tags else None
            links_str = ','.join(links) if links else None
            
            cursor.execute("SELECT id, hash, version FROM notes WHERE path = %s", (rel_path,))
            result = cursor.fetchone()
            
            if result:
                note_id, old_hash, current_version = result
                
                if old_hash != file_hash:
                    new_version = current_version + 1
                    
                    cursor.execute("""
                        INSERT INTO note_versions 
                        (note_id, note_uuid, path, title, folder, content, yaml, tags, links, hash, word_count, version, change_type, created_at, modified_at)
                        SELECT id, uuid, path, title, folder, content, yaml, tags, links, hash, word_count, version, 'UPDATE', created_at, modified_at
                        FROM notes WHERE id = %s
                    """, (note_id,))
                    
                    cursor.execute("""
                        UPDATE notes 
                        SET title = %s, folder = %s, note_type = %s, content = %s, yaml = %s, 
                            tags = %s, links = %s, hash = %s, word_count = %s, version = %s,
                            modified_at = %s, updated_at = %s
                        WHERE id = %s
                    """, (title, folder, note_type, content, yaml_str, tags_str, links_str, 
                          file_hash, word_count, new_version, modified_at, int(datetime.now().timestamp()), note_id))
                    
                    return 'updated', errors
                else:
                    return 'unchanged', errors
            else:
                import uuid
                note_uuid = str(uuid.uuid4())
                now = int(datetime.now().timestamp())
                
                cursor.execute("""
                    INSERT INTO notes (uuid, path, title, folder, note_type, yaml, tags, links, content, word_count, hash, created_at, modified_at, updated_at, version)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1)
                    RETURNING id
                """, (note_uuid, rel_path, title, folder, note_type, yaml_str, tags_str, links_str, content, word_count, file_hash, created_at, modified_at, now))
                
                note_id = cursor.fetchone()[0]
                
                cursor.execute("""
                    INSERT INTO note_versions 
                    (note_id, note_uuid, path, title, folder, content, yaml, tags, links, hash, word_count, version, change_type, created_at, modified_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, 'CREATE', %s, %s)
                """, (note_id, note_uuid, rel_path, title, folder, content, yaml_str, tags_str, links_str, file_hash, word_count, created_at, modified_at))
                
                return 'added', errors
                
        except Exception as e:
            error_msg = f"Sync error: {str(e)}"
            stack_trace = traceback.format_exc()
            try:
                cursor.execute("""
                    INSERT INTO sync_errors (file_path, error_type, error_message, stack_trace)
                    VALUES (%s, %s, %s, %s)
                """, (str(file_path), "SYNC_ERROR", error_msg, stack_trace))
            except:
                pass
            return 'error', [error_msg]
    
    def detect_deletions(self, cursor, vault_path):
        """Detect and archive deleted notes"""
        deleted_count = 0
        
        try:
            vault_files = set()
            for md_file in Path(vault_path).rglob('*.md'):
                rel_path = str(md_file.relative_to(vault_path))
                vault_files.add(rel_path)
            
            cursor.execute("SELECT id, path FROM notes WHERE COALESCE(is_deleted, FALSE) = FALSE")
            db_notes = cursor.fetchall()
            
            for note_id, file_path in db_notes:
                if file_path not in vault_files:
                    cursor.execute("""
                        INSERT INTO deleted_notes 
                        (original_note_id, note_uuid, path, title, folder, content, yaml, tags, links, hash, word_count, last_version)
                        SELECT id, uuid, path, title, folder, content, yaml, tags, links, hash, word_count, version
                        FROM notes WHERE id = %s
                    """, (note_id,))
                    
                    cursor.execute("""
                        UPDATE notes SET is_deleted = TRUE, updated_at = %s WHERE id = %s
                    """, (int(datetime.now().timestamp()), note_id))
                    
                    deleted_count += 1
                    self.log(f"  Archived deleted note: {file_path}", "INFO")
        
        except Exception as e:
            self.log(f"Error detecting deletions: {str(e)}", "ERROR")
        
        return deleted_count
    
    def start_sync(self):
        """Start sync in background thread"""
        if not self.vault_path.get():
            messagebox.showwarning("Warning", "Please select a vault path first")
            return
            
        self.is_syncing = True
        self.sync_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.sync_notes)
        thread.daemon = True
        thread.start()
        
    def stop_sync(self):
        """Stop ongoing sync"""
        self.is_syncing = False
        self.log("Sync stopped by user", "WARNING")
        
    def sync_notes(self):
        """Main sync logic"""
        self.log("=" * 70)
        self.log("Starting sync...")
        sync_start = datetime.now()
        
        added = 0
        updated = 0
        unchanged = 0
        deleted = 0
        errors = 0
        
        try:
            conn = psycopg2.connect(
                host=self.db_host.get(),
                port=self.db_port.get(),
                database=self.db_name.get(),
                user=self.db_user.get(),
                password=self.db_password.get()
            )
            cursor = conn.cursor()
            
            vault_path = Path(self.vault_path.get())
            md_files = list(vault_path.rglob('*.md'))
            total_files = len(md_files)
            
            self.log(f"Found {total_files} markdown files")
            
            for idx, file_path in enumerate(md_files):
                if not self.is_syncing:
                    break
                    
                progress = (idx + 1) / total_files * 100
                self.progress_var.set(progress)
                self.status_label.config(text=f"Syncing: {file_path.name} ({idx+1}/{total_files})")
                
                result, file_errors = self.sync_note(file_path, cursor, vault_path)
                
                if result == 'added':
                    added += 1
                    self.log(f"✓ Added: {file_path.name}")
                elif result == 'updated':
                    updated += 1
                    self.log(f"✓ Updated: {file_path.name}")
                elif result == 'unchanged':
                    unchanged += 1
                elif result == 'error':
                    errors += 1
                    self.log(f"✗ Error: {file_path.name}", "ERROR")
                
                if file_errors:
                    self.log(f"  Warnings: {', '.join(file_errors[:2])}", "WARNING")
                    
                if (idx + 1) % 10 == 0:
                    conn.commit()
            
            self.log("Checking for deleted notes...")
            deleted = self.detect_deletions(cursor, vault_path)
            
            conn.commit()
            
            cursor.execute("""
                INSERT INTO sync_log (sync_started, sync_completed, notes_added, notes_updated, notes_deleted, notes_unchanged, errors, status, vault_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (sync_start, datetime.now(), added, updated, deleted, unchanged, errors, 'completed' if self.is_syncing else 'stopped', str(vault_path)))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            self.log("=" * 70)
            self.log(f"Sync completed!")
            self.log(f"  Added: {added}")
            self.log(f"  Updated: {updated}")
            self.log(f"  Deleted: {deleted}")
            self.log(f"  Unchanged: {unchanged}")
            self.log(f"  Errors: {errors}")
            self.log(f"  Total: {total_files}")
            self.log("=" * 70)
            
            self.status_label.config(text=f"Complete: {added} added, {updated} updated, {deleted} deleted")
            
            if self.is_syncing:
                messagebox.showinfo("Success", f"Sync completed!\n\nAdded: {added}\nUpdated: {updated}\nDeleted: {deleted}\nErrors: {errors}")
            
        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            self.log(f"✗ {error_msg}", "ERROR")
            self.log(traceback.format_exc(), "ERROR")
            messagebox.showerror("Error", error_msg)
            
        finally:
            self.is_syncing = False
            self.sync_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.progress_var.set(0)
    
    def view_stats(self):
        """Show database statistics"""
        try:
            conn = psycopg2.connect(
                host=self.db_host.get(),
                port=self.db_port.get(),
                database=self.db_name.get(),
                user=self.db_user.get(),
                password=self.db_password.get()
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE COALESCE(is_deleted, FALSE) = FALSE) as active,
                    COUNT(*) FILTER (WHERE COALESCE(is_deleted, FALSE) = TRUE) as deleted,
                    SUM(word_count) as total_words
                FROM notes
            """)
            total, active, deleted, total_words = cursor.fetchone()
            
            cursor.execute("SELECT COUNT(*) FROM note_versions")
            versions = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM sync_log")
            syncs = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            stats = f"""Database Statistics:

Total Notes: {total:,}
Active Notes: {active:,}
Deleted Notes: {deleted:,}
Total Words: {total_words:,}

Version History: {versions:,} versions
Sync History: {syncs:,} syncs
"""
            
            messagebox.showinfo("Database Statistics", stats)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to get stats:\n{str(e)}")

def main():
    root = tk.Tk()
    app = ObsidianSync(root)
    root.mainloop()

if __name__ == "__main__":
    main()
