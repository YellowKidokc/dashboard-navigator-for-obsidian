"""
Theophysics Content Database - SQLite Schema and Ingestion
Stores sermons, teachings, transcripts, and extracted concepts before
processing into Obsidian vault and PostgreSQL.
"""

import sqlite3
import json
import re
import hashlib
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple


# ============================================================================
# DATABASE SCHEMA
# ============================================================================

SCHEMA = """
-- Core content table
CREATE TABLE IF NOT EXISTS content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,
    content_type TEXT NOT NULL,  -- 'sermon', 'teaching', 'transcript', 'quote', 'note'
    title TEXT,
    source TEXT,                  -- speaker, author, book
    source_url TEXT,
    raw_text TEXT NOT NULL,
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    status TEXT DEFAULT 'raw'     -- 'raw', 'extracted', 'linked', 'exported'
);

-- Extracted concepts/themes
CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    concept TEXT NOT NULL,
    concept_type TEXT,            -- 'theme', 'doctrine', 'scripture', 'greek_term', 'definition'
    context TEXT,                 -- surrounding text
    confidence REAL DEFAULT 1.0,
    FOREIGN KEY (content_id) REFERENCES content(id)
);

-- Scripture references
CREATE TABLE IF NOT EXISTS scriptures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    reference TEXT NOT NULL,      -- 'Matthew 12:37'
    book TEXT,
    chapter INTEGER,
    verse_start INTEGER,
    verse_end INTEGER,
    quoted_text TEXT,
    context TEXT,
    FOREIGN KEY (content_id) REFERENCES content(id)
);

-- Greek/Hebrew terms
CREATE TABLE IF NOT EXISTS original_terms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    term TEXT NOT NULL,           -- 'metanoia'
    language TEXT,                -- 'greek', 'hebrew'
    transliteration TEXT,
    meaning TEXT,
    context TEXT,
    FOREIGN KEY (content_id) REFERENCES content(id)
);

-- Key quotes/statements
CREATE TABLE IF NOT EXISTS quotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    quote_text TEXT NOT NULL,
    speaker TEXT,
    significance TEXT,            -- why it matters
    tags TEXT,                    -- JSON array
    FOREIGN KEY (content_id) REFERENCES content(id)
);

-- Links to Theophysics concepts
CREATE TABLE IF NOT EXISTS theophysics_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    concept_id INTEGER,
    theophysics_term TEXT,        -- 'Grace Function', 'Moral Conservation', etc.
    law_number INTEGER,           -- L1-L10
    connection_type TEXT,         -- 'supports', 'illustrates', 'contradicts', 'extends'
    explanation TEXT,
    FOREIGN KEY (content_id) REFERENCES content(id),
    FOREIGN KEY (concept_id) REFERENCES concepts(id)
);

-- Processing log
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (content_id) REFERENCES content(id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_content_type ON content(content_type);
CREATE INDEX IF NOT EXISTS idx_content_status ON content(status);
CREATE INDEX IF NOT EXISTS idx_concepts_type ON concepts(concept_type);
CREATE INDEX IF NOT EXISTS idx_scriptures_ref ON scriptures(reference);
CREATE INDEX IF NOT EXISTS idx_theophysics_term ON theophysics_links(theophysics_term);
"""


# ============================================================================
# DATABASE CLASS
# ============================================================================

class TheophysicsContentDB:
    """SQLite database for theological content staging."""

    def __init__(self, db_path: str = None):
        if db_path is None:
            engine_root = Path(__file__).resolve().parents[1]
            db_path = str(engine_root / "data" / "theophysics_content.db")

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema."""
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self):
        """Close database connection."""
        self.conn.close()

    # ---- Content CRUD ----

    def add_content(self, raw_text: str, content_type: str = 'transcript',
                   title: str = None, source: str = None, source_url: str = None) -> int:
        """Add new content to database. Returns content_id."""
        content_hash = hashlib.sha256(raw_text.encode()).hexdigest()[:16]
        word_count = len(raw_text.split())

        try:
            cursor = self.conn.execute("""
                INSERT INTO content (content_hash, content_type, title, source, source_url, raw_text, word_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (content_hash, content_type, title, source, source_url, raw_text, word_count))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Already exists
            cursor = self.conn.execute("SELECT id FROM content WHERE content_hash = ?", (content_hash,))
            return cursor.fetchone()[0]

    def get_content(self, content_id: int) -> Optional[dict]:
        """Get content by ID."""
        cursor = self.conn.execute("SELECT * FROM content WHERE id = ?", (content_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_unprocessed(self, limit: int = 10) -> List[dict]:
        """Get unprocessed content."""
        cursor = self.conn.execute(
            "SELECT * FROM content WHERE status = 'raw' ORDER BY created_at LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_status(self, content_id: int, status: str):
        """Update content status."""
        self.conn.execute(
            "UPDATE content SET status = ?, processed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, content_id)
        )
        self.conn.commit()

    # ---- Concepts ----

    def add_concept(self, content_id: int, concept: str, concept_type: str = None,
                   context: str = None, confidence: float = 1.0) -> int:
        """Add extracted concept."""
        cursor = self.conn.execute("""
            INSERT INTO concepts (content_id, concept, concept_type, context, confidence)
            VALUES (?, ?, ?, ?, ?)
        """, (content_id, concept, concept_type, context, confidence))
        self.conn.commit()
        return cursor.lastrowid

    def get_concepts(self, content_id: int) -> List[dict]:
        """Get concepts for content."""
        cursor = self.conn.execute(
            "SELECT * FROM concepts WHERE content_id = ?", (content_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # ---- Scriptures ----

    def add_scripture(self, content_id: int, reference: str, book: str = None,
                     chapter: int = None, verse_start: int = None, verse_end: int = None,
                     quoted_text: str = None, context: str = None) -> int:
        """Add scripture reference."""
        cursor = self.conn.execute("""
            INSERT INTO scriptures (content_id, reference, book, chapter, verse_start, verse_end, quoted_text, context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_id, reference, book, chapter, verse_start, verse_end, quoted_text, context))
        self.conn.commit()
        return cursor.lastrowid

    def get_scriptures(self, content_id: int) -> List[dict]:
        """Get scriptures for content."""
        cursor = self.conn.execute(
            "SELECT * FROM scriptures WHERE content_id = ?", (content_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    # ---- Greek/Hebrew Terms ----

    def add_original_term(self, content_id: int, term: str, language: str = 'greek',
                         transliteration: str = None, meaning: str = None,
                         context: str = None) -> int:
        """Add Greek/Hebrew term."""
        cursor = self.conn.execute("""
            INSERT INTO original_terms (content_id, term, language, transliteration, meaning, context)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (content_id, term, language, transliteration, meaning, context))
        self.conn.commit()
        return cursor.lastrowid

    # ---- Quotes ----

    def add_quote(self, content_id: int, quote_text: str, speaker: str = None,
                 significance: str = None, tags: List[str] = None) -> int:
        """Add key quote."""
        tags_json = json.dumps(tags) if tags else None
        cursor = self.conn.execute("""
            INSERT INTO quotes (content_id, quote_text, speaker, significance, tags)
            VALUES (?, ?, ?, ?, ?)
        """, (content_id, quote_text, speaker, significance, tags_json))
        self.conn.commit()
        return cursor.lastrowid

    # ---- Theophysics Links ----

    def add_theophysics_link(self, content_id: int, theophysics_term: str,
                            law_number: int = None, connection_type: str = 'supports',
                            explanation: str = None, concept_id: int = None) -> int:
        """Link content to Theophysics concept."""
        cursor = self.conn.execute("""
            INSERT INTO theophysics_links (content_id, concept_id, theophysics_term, law_number, connection_type, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (content_id, concept_id, theophysics_term, law_number, connection_type, explanation))
        self.conn.commit()
        return cursor.lastrowid

    # ---- Logging ----

    def log_action(self, content_id: int, action: str, details: str = None):
        """Log processing action."""
        self.conn.execute("""
            INSERT INTO processing_log (content_id, action, details)
            VALUES (?, ?, ?)
        """, (content_id, action, details))
        self.conn.commit()

    # ---- Stats ----

    def get_stats(self) -> dict:
        """Get database statistics."""
        stats = {}

        cursor = self.conn.execute("SELECT COUNT(*) FROM content")
        stats['total_content'] = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM content WHERE status = 'raw'")
        stats['unprocessed'] = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM concepts")
        stats['total_concepts'] = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM scriptures")
        stats['total_scriptures'] = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT COUNT(*) FROM theophysics_links")
        stats['total_links'] = cursor.fetchone()[0]

        cursor = self.conn.execute("SELECT SUM(word_count) FROM content")
        stats['total_words'] = cursor.fetchone()[0] or 0

        return stats


# ============================================================================
# CONTENT EXTRACTOR
# ============================================================================

class ContentExtractor:
    """Extracts structured data from raw theological content."""

    # Scripture reference patterns
    SCRIPTURE_PATTERNS = [
        r'(\d?\s*[A-Z][a-z]+)\s+(\d+):(\d+)(?:-(\d+))?',  # Matthew 12:37 or Matthew 12:37-40
        r'(\d?\s*[A-Z][a-z]+)\s+(\d+):(\d+)\s*(?:and|,)\s*(\d+)',  # Hebrews 10:17 and 34
    ]

    # Greek/Hebrew term patterns
    GREEK_PATTERNS = [
        r'\b(metanoia|metaninoia|tetelestai|tetlasti|agape|logos|pneuma|theos|christos|sozo|hamartia|pistis|charis|ekklesia)\b',
    ]

    # Key theological concepts
    THEOLOGICAL_CONCEPTS = {
        'repentance': ['repent', 'repentance', 'metanoia', 'turn away'],
        'righteousness': ['righteous', 'righteousness', 'justified', 'justification'],
        'sin': ['sin', 'sinner', 'sinful', 'transgression', 'iniquity'],
        'faith': ['faith', 'believe', 'trust', 'believing'],
        'grace': ['grace', 'unmerited', 'favor'],
        'salvation': ['saved', 'salvation', 'redemption', 'redeemed'],
        'identity': ['identity', 'who you are', 'called', 'named'],
        'sanctification': ['sanctified', 'sanctification', 'holy', 'holiness'],
        'forgiveness': ['forgive', 'forgiveness', 'forgiven', 'washed'],
        'condemnation': ['condemn', 'condemnation', 'condemned', 'guilt'],
        'blood_of_christ': ['blood', 'blood of jesus', 'blood of christ', 'sacrifice'],
        'spiritual_warfare': ['satan', 'devil', 'enemy', 'warfare', 'temptation', 'tempted'],
        'thoughts': ['thoughts', 'thinking', 'mind', 'mindset', 'mental'],
        'confession': ['confess', 'confession', 'declare', 'mouth', 'tongue'],
        'baptism': ['baptism', 'baptized', 'baptize'],
    }

    # Theophysics mapping
    THEOPHYSICS_MAPPING = {
        'righteousness': ('Grace Function', 7, 'Law of Grace - righteousness through grace not works'),
        'identity': ('Soul Operator', 5, 'Law of Soul Operator - identity determines trajectory'),
        'faith': ('Conscious Observation', 2, 'Law of Conscious Observation - faith as participatory'),
        'thoughts': ('Moral Conservation', 4, 'Law of Moral Conservation - thoughts affect moral state'),
        'spiritual_warfare': ('Spiritual Conflict', 7, 'Law of Spiritual Conflict - adversarial operators'),
        'confession': ('Participatory Reality', 8, 'Law of Participatory Reality - words create reality'),
        'grace': ('Grace Function', 7, 'Grace as exponential counterforce'),
        'sanctification': ('Negentropic Purpose', 6, 'Negentropy - movement toward coherence'),
    }

    def __init__(self, db: TheophysicsContentDB):
        self.db = db

    def extract_all(self, content_id: int) -> dict:
        """Extract all structured data from content."""
        content = self.db.get_content(content_id)
        if not content:
            return {}

        raw_text = content['raw_text']
        results = {
            'scriptures': self.extract_scriptures(content_id, raw_text),
            'greek_terms': self.extract_greek_terms(content_id, raw_text),
            'concepts': self.extract_concepts(content_id, raw_text),
            'quotes': self.extract_quotes(content_id, raw_text),
            'theophysics_links': []
        }

        # Link to Theophysics
        for concept in results['concepts']:
            if concept['concept'] in self.THEOPHYSICS_MAPPING:
                term, law, explanation = self.THEOPHYSICS_MAPPING[concept['concept']]
                link_id = self.db.add_theophysics_link(
                    content_id=content_id,
                    theophysics_term=term,
                    law_number=law,
                    connection_type='illustrates',
                    explanation=explanation,
                    concept_id=concept['id']
                )
                results['theophysics_links'].append({
                    'id': link_id,
                    'term': term,
                    'law': law
                })

        # Update status
        self.db.update_status(content_id, 'extracted')
        self.db.log_action(content_id, 'extract_all', json.dumps({
            'scriptures': len(results['scriptures']),
            'concepts': len(results['concepts']),
            'links': len(results['theophysics_links'])
        }))

        return results

    def extract_scriptures(self, content_id: int, text: str) -> List[dict]:
        """Extract scripture references."""
        scriptures = []

        for pattern in self.SCRIPTURE_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                groups = match.groups()
                book = groups[0].strip()
                chapter = int(groups[1])
                verse_start = int(groups[2])
                verse_end = int(groups[3]) if len(groups) > 3 and groups[3] else None

                reference = f"{book} {chapter}:{verse_start}"
                if verse_end:
                    reference += f"-{verse_end}"

                # Get context (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                scripture_id = self.db.add_scripture(
                    content_id=content_id,
                    reference=reference,
                    book=book,
                    chapter=chapter,
                    verse_start=verse_start,
                    verse_end=verse_end,
                    context=context
                )

                scriptures.append({
                    'id': scripture_id,
                    'reference': reference,
                    'context': context
                })

        return scriptures

    def extract_greek_terms(self, content_id: int, text: str) -> List[dict]:
        """Extract Greek/Hebrew terms."""
        terms = []
        text_lower = text.lower()

        # Known terms with meanings
        term_meanings = {
            'metanoia': ('Greek', 'metanoia', 'change of mind, repentance'),
            'metaninoia': ('Greek', 'metanoia', 'change of mind, repentance'),
            'tetelestai': ('Greek', 'tetelestai', 'it is finished, paid in full'),
            'tetlasti': ('Greek', 'tetelestai', 'it is finished, paid in full'),
            'agape': ('Greek', 'agape', 'unconditional love'),
            'logos': ('Greek', 'logos', 'word, reason, principle'),
            'pneuma': ('Greek', 'pneuma', 'spirit, breath'),
        }

        for pattern in self.GREEK_PATTERNS:
            for match in re.finditer(pattern, text_lower):
                term = match.group(1)

                if term in term_meanings:
                    lang, translit, meaning = term_meanings[term]
                else:
                    lang, translit, meaning = 'Greek', term, None

                # Get context
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                term_id = self.db.add_original_term(
                    content_id=content_id,
                    term=term,
                    language=lang,
                    transliteration=translit,
                    meaning=meaning,
                    context=context
                )

                terms.append({
                    'id': term_id,
                    'term': term,
                    'meaning': meaning
                })

        return terms

    def extract_concepts(self, content_id: int, text: str) -> List[dict]:
        """Extract theological concepts."""
        concepts = []
        text_lower = text.lower()

        for concept, keywords in self.THEOLOGICAL_CONCEPTS.items():
            count = sum(text_lower.count(kw.lower()) for kw in keywords)
            if count >= 2:  # Only if mentioned multiple times
                # Find first occurrence for context
                for kw in keywords:
                    pos = text_lower.find(kw.lower())
                    if pos >= 0:
                        start = max(0, pos - 50)
                        end = min(len(text), pos + len(kw) + 50)
                        context = text[start:end]
                        break
                else:
                    context = None

                concept_id = self.db.add_concept(
                    content_id=content_id,
                    concept=concept,
                    concept_type='theme',
                    context=context,
                    confidence=min(1.0, count / 10)  # Higher count = higher confidence
                )

                concepts.append({
                    'id': concept_id,
                    'concept': concept,
                    'occurrences': count
                })

        return sorted(concepts, key=lambda x: x['occurrences'], reverse=True)

    def extract_quotes(self, content_id: int, text: str) -> List[dict]:
        """Extract key quotes/statements."""
        quotes = []

        # Look for powerful statements (sentences with key phrases)
        key_phrases = [
            'that\'s the gospel',
            'you have to',
            'the truth is',
            'remember',
            'understand?',
            'sheesh',
            'amen',
            'hallelujah',
        ]

        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue

            sentence_lower = sentence.lower()
            for phrase in key_phrases:
                if phrase in sentence_lower:
                    quote_id = self.db.add_quote(
                        content_id=content_id,
                        quote_text=sentence,
                        tags=['key_statement']
                    )
                    quotes.append({
                        'id': quote_id,
                        'text': sentence[:100] + '...' if len(sentence) > 100 else sentence
                    })
                    break

        return quotes[:20]  # Limit to 20 quotes


# ============================================================================
# CLI
# ============================================================================

def main():
    """Test the content database."""
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    print("=" * 60)
    print("THEOPHYSICS CONTENT DATABASE")
    print("=" * 60)

    # Initialize
    db = TheophysicsContentDB()
    extractor = ContentExtractor(db)

    # Test content (the sermon transcript)
    test_content = """Now let me ask you something. Real repentance is distrusting your thoughts accepting the word of God. Because true sin is accepting your thoughts above the word of God. So the opposite is repentance. Right? Remember sin because they don't believe in me. Meaning they don't trust in me. So I'm going to ask you guys one question to differentiate who is a real Christian today and who's not. Let's see if a person exalts their thoughts and their feelings which change every day or the word of God that never changes. Let's see who's really a Christian today. Who here is perfected forever and righteous through the blood and is no longer a sinner because of the blood. And who here still claims to be a sinner? Interesting. You guys got it right. We're all sinners. Good. Where do sinners go? They go to hell. Do you guys know why God allowed Adam to name the animals? Because he was teaching them Proverbs 18:21, life and death is in the power of the tongue. So when he goes, "Father, hippo manifestation." They stole it from the Bible. Okay. Rhino. Okay. Dog. Dog. Cat. Cat. That's what they're saying. So, he's teaching them the power of the tongue. So, whatever you say, it says, so shall it be. Powerful, right? Sheesh. Matthew 12:37. I'm going to read it. Okay. For by thy words, thou shalt be justified. By thy words, thou shalt be condemned. Interesting. Your mouth, same mouth, but what comes out of it will either justify you or it'll condemn you. So imagine I stand in front of God. God, I'm a sinner, but I tried. I tried. God, so you tried, right? But didn't you fall short? Yes, I did. Well, people who fall short, where do they go? I tried. I'm a dirty, evil sinner. I'm a dirty, evil sinner. So shall it be. Where do sinners go? They go to hell. No. Although I tried. I failed. Yes. But you didn't fail. You made me righteous. You made me holy. I'm perfected not because I did well, but because you did well. I'm not perfect because I'm obedient, but because you were obedient and you kept the law for me. You cleared my debt. You said tetlasti, it is finished. You finished it for me cuz I couldn't finish it. I started the race. You finished the race. Amen. Hallelujah. If you believe this, you can only say it if you believe. So now I'm going to ask you, where do righteous people go? They go to heaven. That's the gospel. How can I meet Jesus and say I'm a sinner still? He saved me from my sins. But because people go to hell not because they're good or bad. They go to hell because they don't believe the word of God. And that's what sin is. They believe their thoughts above the word of God. That's what true sin is. You don't just lust. You have an evil thought that enters. Oh, I like this. I like that. I want to play with this woman. Blah blah blah. And then it leads to what? Feelings of that and then behavior. So the way you think affects the way you feel and the way you feel behavior. No one just wakes up and sins. That's why God says cut it at the root, which is your thoughts. Oh, you're a sinner. You're a sinner. You're a sinner. Yeah, I'm a sinner. And then you fail. You accept Satan. No, I'm not a sinner. Excuse you. God called me righteous and knows me by my name. You call me by my sins, Satan. But God calls me by my name. He calls me by the blood. He calls me by the spirit. I am righteous. You see the difference? You then gain strength to overcome rather than listening to him. Yeah. At night, one thought turns into 20 thoughts, 40 thoughts. Now you want to unal alive yourself. You feel pressure in your chest. You're crying because you're trying so hard to stop your thoughts, your thoughts, which is actually his thoughts. Do you understand now? You don't even recognize how you're getting dragged. Did you guys know God doesn't even remember your sins? What? Hebrews 10:17. And their sins and iniquities will I remember no more. Hebrews 10:17. Jeremiah 31:34 as well. It reiterates this. I don't remember your sins. Why? because Jesus washed it all and immediately thoughts will come. Well, but I still sin. I still sin. But what if what if I sin again? What if I stop listening to all of that? Just accept this. You don't have to try to understand it. Understand what I'm saying? Well, what if I do this? What if tomorrow I smoke weed? What? All these hypotheticals are from Satan. He's trying to knock in your head again. No, I'm righteous cuz Jesus didn't fail. A 5-year-old can understand that. Stop thinking. When you think you're thinking, you're actually listening. Sheesh. Satan will whisper into you. No, that's not true. know that you still have to repent. No, you you don't even know what repentance is. Truthfully speaking, you guys don't even know that there's two types of repentance, three types of baptism. Real repentance. There's two types. Metaninoia and there's dead works repentance. We don't even know that. Two types of confession. We don't know that. That's biblical. Nobody even understands that. Why? Because we're not reading the Bible."""

    print("\n[1] Adding content to database...")
    content_id = db.add_content(
        raw_text=test_content,
        content_type='sermon',
        title='Righteousness and Identity Teaching',
        source='Unknown Speaker'
    )
    print(f"    Content ID: {content_id}")

    print("\n[2] Extracting structured data...")
    results = extractor.extract_all(content_id)

    print(f"\n[3] EXTRACTION RESULTS:")
    print(f"    Scriptures found: {len(results['scriptures'])}")
    for s in results['scriptures']:
        print(f"      - {s['reference']}")

    print(f"\n    Greek terms found: {len(results['greek_terms'])}")
    for t in results['greek_terms']:
        print(f"      - {t['term']}: {t['meaning']}")

    print(f"\n    Concepts extracted: {len(results['concepts'])}")
    for c in results['concepts'][:10]:
        print(f"      - {c['concept']} ({c['occurrences']} mentions)")

    print(f"\n    Theophysics links: {len(results['theophysics_links'])}")
    for l in results['theophysics_links']:
        print(f"      - L{l['law']}: {l['term']}")

    print(f"\n    Key quotes: {len(results['quotes'])}")
    for q in results['quotes'][:5]:
        print(f"      - \"{q['text']}\"")

    print("\n[4] DATABASE STATS:")
    stats = db.get_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")

    db.close()
    print("\n[DONE] Database saved to: D:\\THEOPHYSICS_MASTER\\00_VAULT_SYSTEM\\Engine\\data\\theophysics_content.db")


if __name__ == "__main__":
    main()
