"""
Vault Analytics - Dense, data-driven vault analysis with dark theme HTML reports

Metrics layers (bottom to top):
1. BASIC: word counts, unique words, vocabulary density
2. LEXICAL: novel words, hapax legomena, type-token ratio
3. COHERENCE: sentence length variance, paragraph density
4. N-GRAMS: bigrams, trigrams, 4-grams frequency
5. SEMANTIC: word co-occurrence windows (30w, 60w), topic clustering
6. COMPARATIVE: cross-paper deltas, outliers, distributions

Output: Single dense HTML report with dark theme
"""

import re
import math
import json
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, List, Tuple
import base64
from io import BytesIO

# Try to import visualization libs
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, charts disabled")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


# Dark theme colors
COLORS = {
    'bg': '#1a1a1a',
    'card': '#252525',
    'text': '#e0e0e0',
    'muted': '#888888',
    'accent': '#7b68ee',
    'accent2': '#4ecdc4',
    'accent3': '#ff6b6b',
    'grid': '#333333',
}

# Stop words to filter
STOP_WORDS = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why', 'how',
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
    'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very'])


class VaultAnalytics:
    def __init__(self, vault_path: Path):
        self.vault = vault_path
        self.papers = {}  # path -> {content, words, stats}
        self.global_stats = {}
        self.word_freq = Counter()
        self.bigrams = Counter()
        self.trigrams = Counter()
        self.cooccur_30 = defaultdict(Counter)  # word -> words within 30
        self.cooccur_60 = defaultdict(Counter)  # word -> words within 60

    def tokenize(self, text: str) -> List[str]:
        """Extract words, lowercase, filter."""
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text.lower())
        return [w for w in words if w not in STOP_WORDS]

    def analyze_file(self, filepath: Path) -> Dict:
        """Analyze a single file."""
        try:
            content = filepath.read_text(encoding='utf-8', errors='ignore')
        except:
            return None

        # Strip frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2]

        words = self.tokenize(content)
        if len(words) < 10:
            return None

        # Basic stats
        word_count = len(words)
        unique_words = set(words)
        unique_count = len(unique_words)

        # Sentences and paragraphs
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
        paragraphs = [p.strip() for p in content.split('\n\n') if len(p.strip()) > 20]

        # Hapax legomena (words appearing once)
        word_counts = Counter(words)
        hapax = [w for w, c in word_counts.items() if c == 1]

        stats = {
            'word_count': word_count,
            'unique_count': unique_count,
            'vocabulary_density': unique_count / word_count if word_count else 0,
            'hapax_count': len(hapax),
            'hapax_ratio': len(hapax) / unique_count if unique_count else 0,
            'sentence_count': len(sentences),
            'avg_sentence_len': word_count / len(sentences) if sentences else 0,
            'paragraph_count': len(paragraphs),
            'avg_para_len': word_count / len(paragraphs) if paragraphs else 0,
        }

        return {
            'words': words,
            'unique': unique_words,
            'word_counts': word_counts,
            'stats': stats,
        }

    def scan_vault(self, limit: int = 0):
        """Scan all papers in vault."""
        md_files = list(self.vault.rglob('*.md'))

        # Filter out canonical/system files
        skip = ['00_CANONICAL', '01_CANONICAL', '04_The_Axioms', 'node_modules', '.git']
        md_files = [f for f in md_files if not any(s in str(f) for s in skip)]

        if limit:
            md_files = md_files[:limit]

        print(f"Analyzing {len(md_files)} files...")

        for i, filepath in enumerate(md_files):
            result = self.analyze_file(filepath)
            if result:
                rel_path = str(filepath.relative_to(self.vault))
                self.papers[rel_path] = result

                # Accumulate global stats
                self.word_freq.update(result['word_counts'])

                # N-grams
                words = result['words']
                for j in range(len(words) - 1):
                    self.bigrams[(words[j], words[j+1])] += 1
                for j in range(len(words) - 2):
                    self.trigrams[(words[j], words[j+1], words[j+2])] += 1

                # Co-occurrence windows
                for j, word in enumerate(words):
                    # 30-word window
                    window_30 = words[max(0, j-15):j] + words[j+1:j+16]
                    for w in window_30:
                        if w != word:
                            self.cooccur_30[word][w] += 1
                    # 60-word window
                    window_60 = words[max(0, j-30):j] + words[j+1:j+31]
                    for w in window_60:
                        if w != word:
                            self.cooccur_60[word][w] += 1

            if (i + 1) % 50 == 0:
                print(f"  ...{i+1}/{len(md_files)}")

        self._compute_global_stats()

    def _compute_global_stats(self):
        """Compute vault-wide statistics."""
        if not self.papers:
            return

        all_stats = [p['stats'] for p in self.papers.values()]

        def agg(key):
            vals = [s[key] for s in all_stats]
            return {
                'min': min(vals),
                'max': max(vals),
                'mean': sum(vals) / len(vals),
                'median': sorted(vals)[len(vals)//2],
                'std': (sum((x - sum(vals)/len(vals))**2 for x in vals) / len(vals)) ** 0.5
            }

        self.global_stats = {
            'paper_count': len(self.papers),
            'total_words': sum(s['word_count'] for s in all_stats),
            'total_unique': len(self.word_freq),
            'word_count': agg('word_count'),
            'vocabulary_density': agg('vocabulary_density'),
            'hapax_ratio': agg('hapax_ratio'),
            'avg_sentence_len': agg('avg_sentence_len'),
            'avg_para_len': agg('avg_para_len'),
            'top_words': self.word_freq.most_common(50),
            'top_bigrams': self.bigrams.most_common(30),
            'top_trigrams': self.trigrams.most_common(20),
        }

    def _fig_to_base64(self, fig) -> str:
        """Convert matplotlib figure to base64 for embedding."""
        buf = BytesIO()
        fig.savefig(buf, format='png', facecolor=COLORS['bg'],
                    edgecolor='none', bbox_inches='tight', dpi=100)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig)
        return f"data:image/png;base64,{b64}"

    def _make_bar_chart(self, data: List[Tuple], title: str, xlabel: str = '', horizontal: bool = True) -> str:
        """Create compact bar chart."""
        if not MATPLOTLIB_AVAILABLE or not data:
            return ""

        labels = [str(d[0])[:20] for d in data[:15]]
        values = [d[1] for d in data[:15]]

        fig, ax = plt.subplots(figsize=(4, 2.5))
        fig.patch.set_facecolor(COLORS['bg'])
        ax.set_facecolor(COLORS['card'])

        if horizontal:
            ax.barh(labels[::-1], values[::-1], color=COLORS['accent'], height=0.7)
        else:
            ax.bar(labels, values, color=COLORS['accent'], width=0.7)
            plt.xticks(rotation=45, ha='right')

        ax.tick_params(colors=COLORS['text'], labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.spines['left'].set_color(COLORS['grid'])

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _make_histogram(self, values: List[float], title: str, bins: int = 20) -> str:
        """Create compact histogram."""
        if not MATPLOTLIB_AVAILABLE or not values:
            return ""

        fig, ax = plt.subplots(figsize=(4, 2))
        fig.patch.set_facecolor(COLORS['bg'])
        ax.set_facecolor(COLORS['card'])

        ax.hist(values, bins=bins, color=COLORS['accent2'], edgecolor=COLORS['card'], linewidth=0.5)

        ax.tick_params(colors=COLORS['text'], labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.spines['left'].set_color(COLORS['grid'])

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def _make_scatter(self, x_vals: List, y_vals: List, xlabel: str, ylabel: str) -> str:
        """Create compact scatter plot."""
        if not MATPLOTLIB_AVAILABLE or not x_vals:
            return ""

        fig, ax = plt.subplots(figsize=(4, 2.5))
        fig.patch.set_facecolor(COLORS['bg'])
        ax.set_facecolor(COLORS['card'])

        ax.scatter(x_vals, y_vals, c=COLORS['accent'], alpha=0.6, s=15)

        ax.set_xlabel(xlabel, color=COLORS['muted'], fontsize=7)
        ax.set_ylabel(ylabel, color=COLORS['muted'], fontsize=7)
        ax.tick_params(colors=COLORS['text'], labelsize=7)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['grid'])
        ax.spines['left'].set_color(COLORS['grid'])

        plt.tight_layout()
        return self._fig_to_base64(fig)

    def generate_html(self, output_path: Path):
        """Generate dense dark-theme HTML report."""
        gs = self.global_stats

        # Collect data for charts
        word_counts = [p['stats']['word_count'] for p in self.papers.values()]
        vocab_density = [p['stats']['vocabulary_density'] for p in self.papers.values()]
        hapax_ratios = [p['stats']['hapax_ratio'] for p in self.papers.values()]
        sent_lens = [p['stats']['avg_sentence_len'] for p in self.papers.values()]

        # Generate charts
        charts = {}
        if MATPLOTLIB_AVAILABLE:
            charts['top_words'] = self._make_bar_chart(gs['top_words'][:15], 'Top Words')
            charts['top_bigrams'] = self._make_bar_chart(
                [(f"{b[0]} {b[1]}", c) for b, c in gs['top_bigrams'][:12]], 'Top Bigrams')
            charts['top_trigrams'] = self._make_bar_chart(
                [(f"{t[0]} {t[1]} {t[2]}", c) for t, c in gs['top_trigrams'][:10]], 'Top Trigrams')
            charts['word_dist'] = self._make_histogram(word_counts, 'Word Count Distribution')
            charts['vocab_dist'] = self._make_histogram(vocab_density, 'Vocabulary Density')
            charts['hapax_dist'] = self._make_histogram(hapax_ratios, 'Hapax Ratio')
            charts['scatter_wc_vd'] = self._make_scatter(word_counts, vocab_density, 'Word Count', 'Vocab Density')
            charts['scatter_wc_hapax'] = self._make_scatter(word_counts, hapax_ratios, 'Word Count', 'Hapax Ratio')

            # Co-occurrence for top words
            top_word = gs['top_words'][0][0] if gs['top_words'] else None
            if top_word and top_word in self.cooccur_30:
                cooccur_data = self.cooccur_30[top_word].most_common(12)
                charts['cooccur_30'] = self._make_bar_chart(cooccur_data, f'"{top_word}" co-occurs (30w)')

        # Build HTML
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Vault Analytics Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: {COLORS['bg']};
            color: {COLORS['text']};
            font-family: 'SF Mono', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.4;
            padding: 20px;
        }}
        h1 {{ font-size: 18px; color: {COLORS['accent']}; margin-bottom: 5px; }}
        h2 {{ font-size: 14px; color: {COLORS['accent2']}; margin: 15px 0 8px 0; border-bottom: 1px solid {COLORS['grid']}; padding-bottom: 4px; }}
        h3 {{ font-size: 11px; color: {COLORS['text']}; font-weight: bold; margin-bottom: 3px; }}
        .meta {{ color: {COLORS['muted']}; font-size: 10px; margin-bottom: 15px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
        .card {{
            background: {COLORS['card']};
            border-radius: 6px;
            padding: 10px;
        }}
        .card p {{ color: {COLORS['muted']}; font-size: 10px; margin-bottom: 6px; }}
        .card img {{ width: 100%; height: auto; border-radius: 4px; }}
        .stat-row {{ display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid {COLORS['grid']}; }}
        .stat-label {{ color: {COLORS['muted']}; }}
        .stat-value {{ color: {COLORS['text']}; font-weight: bold; }}
        .highlight {{ color: {COLORS['accent']}; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 10px; }}
        th {{ text-align: left; color: {COLORS['muted']}; padding: 4px; border-bottom: 1px solid {COLORS['grid']}; }}
        td {{ padding: 4px; border-bottom: 1px solid {COLORS['grid']}; }}
        .layer {{ margin-bottom: 20px; }}
        .layer-title {{ font-size: 10px; color: {COLORS['accent3']}; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }}
    </style>
</head>
<body>
    <h1>VAULT ANALYTICS</h1>
    <div class="meta">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Papers: {gs['paper_count']} | Total Words: {gs['total_words']:,}</div>

    <!-- LAYER 1: BASIC STATISTICS -->
    <div class="layer">
        <div class="layer-title">Layer 1: Basic Statistics</div>
        <div class="grid">
            <div class="card">
                <h3>Corpus Overview</h3>
                <p>Fundamental counts across all analyzed papers.</p>
                <div class="stat-row"><span class="stat-label">Papers Analyzed</span><span class="stat-value">{gs['paper_count']}</span></div>
                <div class="stat-row"><span class="stat-label">Total Words</span><span class="stat-value">{gs['total_words']:,}</span></div>
                <div class="stat-row"><span class="stat-label">Unique Vocabulary</span><span class="stat-value">{gs['total_unique']:,}</span></div>
                <div class="stat-row"><span class="stat-label">Avg Words/Paper</span><span class="stat-value">{gs['word_count']['mean']:.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Median Words</span><span class="stat-value">{gs['word_count']['median']:.0f}</span></div>
                <div class="stat-row"><span class="stat-label">Std Dev</span><span class="stat-value">{gs['word_count']['std']:.1f}</span></div>
            </div>
            <div class="card">
                <h3>Word Count Distribution</h3>
                <p>How paper lengths vary across the corpus. Peaks indicate common document sizes.</p>
                {f'<img src="{charts["word_dist"]}">' if charts.get('word_dist') else '<p>Chart unavailable</p>'}
            </div>
        </div>
    </div>

    <!-- LAYER 2: LEXICAL RICHNESS -->
    <div class="layer">
        <div class="layer-title">Layer 2: Lexical Richness</div>
        <div class="grid">
            <div class="card">
                <h3>Vocabulary Density</h3>
                <p>Unique words / total words. Higher = more diverse vocabulary. Range: {gs['vocabulary_density']['min']:.3f} - {gs['vocabulary_density']['max']:.3f}</p>
                {f'<img src="{charts["vocab_dist"]}">' if charts.get('vocab_dist') else ''}
            </div>
            <div class="card">
                <h3>Hapax Legomena Ratio</h3>
                <p>Words appearing exactly once / unique words. Measures novelty. Mean: {gs['hapax_ratio']['mean']:.3f}</p>
                {f'<img src="{charts["hapax_dist"]}">' if charts.get('hapax_dist') else ''}
            </div>
            <div class="card">
                <h3>Vocabulary vs Length</h3>
                <p>Correlation between paper length and vocabulary density. Longer papers often show lower density (repetition).</p>
                {f'<img src="{charts["scatter_wc_vd"]}">' if charts.get('scatter_wc_vd') else ''}
            </div>
        </div>
    </div>

    <!-- LAYER 3: N-GRAM PATTERNS -->
    <div class="layer">
        <div class="layer-title">Layer 3: N-Gram Patterns</div>
        <div class="grid">
            <div class="card">
                <h3>Top Unigrams</h3>
                <p>Most frequent content words (stopwords filtered). These define the conceptual core.</p>
                {f'<img src="{charts["top_words"]}">' if charts.get('top_words') else ''}
            </div>
            <div class="card">
                <h3>Top Bigrams</h3>
                <p>Most common 2-word sequences. Reveals key phrases and terminology.</p>
                {f'<img src="{charts["top_bigrams"]}">' if charts.get('top_bigrams') else ''}
            </div>
            <div class="card">
                <h3>Top Trigrams</h3>
                <p>3-word sequences showing conceptual chains and recurring formulations.</p>
                {f'<img src="{charts["top_trigrams"]}">' if charts.get('top_trigrams') else ''}
            </div>
        </div>
    </div>

    <!-- LAYER 4: SEMANTIC CO-OCCURRENCE -->
    <div class="layer">
        <div class="layer-title">Layer 4: Semantic Co-occurrence</div>
        <div class="grid">
            <div class="card">
                <h3>30-Word Window Co-occurrence</h3>
                <p>Words appearing near "{gs['top_words'][0][0] if gs['top_words'] else 'N/A'}" within 30 words. Maps immediate semantic context.</p>
                {f'<img src="{charts["cooccur_30"]}">' if charts.get('cooccur_30') else ''}
            </div>
            <div class="card">
                <h3>Novelty vs Length</h3>
                <p>Hapax ratio against word count. High novelty in short papers may indicate dense unique concepts.</p>
                {f'<img src="{charts["scatter_wc_hapax"]}">' if charts.get('scatter_wc_hapax') else ''}
            </div>
        </div>
    </div>

    <!-- LAYER 5: COMPARATIVE OUTLIERS -->
    <div class="layer">
        <div class="layer-title">Layer 5: Comparative Analysis</div>
        <div class="grid">
            <div class="card">
                <h3>Outlier Papers</h3>
                <p>Papers deviating &gt;1.5 std from mean metrics. These require attention.</p>
                <table>
                    <tr><th>Metric</th><th>Low Outliers</th><th>High Outliers</th></tr>
                    <tr><td>Word Count</td><td>{self._count_outliers('word_count', 'low')}</td><td>{self._count_outliers('word_count', 'high')}</td></tr>
                    <tr><td>Vocab Density</td><td>{self._count_outliers('vocabulary_density', 'low')}</td><td>{self._count_outliers('vocabulary_density', 'high')}</td></tr>
                    <tr><td>Hapax Ratio</td><td>{self._count_outliers('hapax_ratio', 'low')}</td><td>{self._count_outliers('hapax_ratio', 'high')}</td></tr>
                </table>
            </div>
            <div class="card">
                <h3>Metric Ranges</h3>
                <p>Statistical bounds for key metrics across corpus.</p>
                <table>
                    <tr><th>Metric</th><th>Min</th><th>Mean</th><th>Max</th><th>Std</th></tr>
                    <tr><td>Words</td><td>{gs['word_count']['min']:.0f}</td><td>{gs['word_count']['mean']:.0f}</td><td>{gs['word_count']['max']:.0f}</td><td>{gs['word_count']['std']:.0f}</td></tr>
                    <tr><td>Vocab Density</td><td>{gs['vocabulary_density']['min']:.3f}</td><td>{gs['vocabulary_density']['mean']:.3f}</td><td>{gs['vocabulary_density']['max']:.3f}</td><td>{gs['vocabulary_density']['std']:.3f}</td></tr>
                    <tr><td>Hapax</td><td>{gs['hapax_ratio']['min']:.3f}</td><td>{gs['hapax_ratio']['mean']:.3f}</td><td>{gs['hapax_ratio']['max']:.3f}</td><td>{gs['hapax_ratio']['std']:.3f}</td></tr>
                    <tr><td>Sent Len</td><td>{gs['avg_sentence_len']['min']:.1f}</td><td>{gs['avg_sentence_len']['mean']:.1f}</td><td>{gs['avg_sentence_len']['max']:.1f}</td><td>{gs['avg_sentence_len']['std']:.1f}</td></tr>
                </table>
            </div>
        </div>
    </div>

    <div class="meta" style="margin-top: 20px; text-align: center;">
        Theophysics Vault Analytics | {len(self.papers)} papers | {gs['total_words']:,} words | {gs['total_unique']:,} unique
    </div>
</body>
</html>"""

        output_path.write_text(html, encoding='utf-8')
        print(f"Report saved: {output_path}")

    def _count_outliers(self, metric: str, direction: str) -> int:
        """Count papers outside 1.5 std."""
        stats = self.global_stats[metric]
        threshold = 1.5 * stats['std']

        count = 0
        for p in self.papers.values():
            val = p['stats'][metric]
            if direction == 'low' and val < stats['mean'] - threshold:
                count += 1
            elif direction == 'high' and val > stats['mean'] + threshold:
                count += 1
        return count


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate vault analytics report')
    parser.add_argument('--vault', '-v', default=r'O:/Theophysics_Master/TM SUBSTACK/03_PUBLICATIONS/Logos Papers Axiom')
    parser.add_argument('--output', '-o', default=r'O:/Theophysics_Master/TM/00_VAULT_OS/Reports/vault_analytics.html')
    parser.add_argument('--limit', '-l', type=int, default=0)
    args = parser.parse_args()

    print("="*60)
    print("  VAULT ANALYTICS")
    print("="*60)

    analytics = VaultAnalytics(Path(args.vault))
    analytics.scan_vault(limit=args.limit)
    analytics.generate_html(Path(args.output))

    print("\nDone.")


if __name__ == '__main__':
    main()
