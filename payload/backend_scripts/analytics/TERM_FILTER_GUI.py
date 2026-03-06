"""
Term Filter GUI
===============
Visual interface for marking terms RED (exclude) or BLUE (include).

Features:
- Visual red/blue/gray color coding
- One-click marking
- Progress tracking
- Saves automatically
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
from term_filter_manager import TermFilterManager


class TermFilterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔴🔵 Term Filter Manager")
        self.root.geometry("900x700")
        self.root.configure(bg='#1a1a2e')
        
        self.manager = TermFilterManager()
        self.current_paper = None
        self.analysis = None
        self.current_index = 0
        self.undecided_terms = []
        
        self.setup_ui()
    
    def setup_ui(self):
        # Header
        header = tk.Frame(self.root, bg='#0f3460', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="🔴🔵 Interactive Term Filter",
            font=('Consolas', 20, 'bold'),
            bg='#0f3460',
            fg='#00d9ff'
        )
        title.pack(pady=20)
        
        # Stats bar
        self.stats_frame = tk.Frame(self.root, bg='#16213e')
        self.stats_frame.pack(fill='x', padx=10, pady=10)
        
        self.stats_label = tk.Label(
            self.stats_frame,
            text="No paper loaded",
            font=('Consolas', 11),
            bg='#16213e',
            fg='#00d9ff'
        )
        self.stats_label.pack(pady=10)
        
        # Load paper button
        load_btn = tk.Button(
            self.stats_frame,
            text="📂 Load Paper",
            command=self.load_paper,
            bg='#0f3460',
            fg='white',
            font=('Consolas', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10
        )
        load_btn.pack(pady=10)
        
        # Term display area
        self.term_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.term_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Current term display
        self.term_display = tk.Label(
            self.term_frame,
            text="",
            font=('Consolas', 36, 'bold'),
            bg='#1a1a2e',
            fg='#ffffff',
            height=3
        )
        self.term_display.pack(pady=20)
        
        self.count_display = tk.Label(
            self.term_frame,
            text="",
            font=('Consolas', 14),
            bg='#1a1a2e',
            fg='#888888'
        )
        self.count_display.pack()
        
        # Progress
        self.progress_label = tk.Label(
            self.term_frame,
            text="",
            font=('Consolas', 12),
            bg='#1a1a2e',
            fg='#00d9ff'
        )
        self.progress_label.pack(pady=10)
        
        # Button frame
        btn_frame = tk.Frame(self.term_frame, bg='#1a1a2e')
        btn_frame.pack(pady=30)
        
        # RED button
        self.red_btn = tk.Button(
            btn_frame,
            text="🔴 EXCLUDE (RED)",
            command=self.mark_red,
            bg='#e94560',
            fg='white',
            font=('Consolas', 14, 'bold'),
            relief='flat',
            cursor='hand2',
            width=20,
            height=3,
            state='disabled'
        )
        self.red_btn.pack(side='left', padx=10)
        
        # BLUE button
        self.blue_btn = tk.Button(
            btn_frame,
            text="🔵 INCLUDE (BLUE)",
            command=self.mark_blue,
            bg='#4ec9b0',
            fg='white',
            font=('Consolas', 14, 'bold'),
            relief='flat',
            cursor='hand2',
            width=20,
            height=3,
            state='disabled'
        )
        self.blue_btn.pack(side='left', padx=10)
        
        # Skip button
        skip_frame = tk.Frame(self.term_frame, bg='#1a1a2e')
        skip_frame.pack(pady=10)
        
        self.skip_btn = tk.Button(
            skip_frame,
            text="⏭️ Skip (decide later)",
            command=self.skip_term,
            bg='#666666',
            fg='white',
            font=('Consolas', 11),
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.skip_btn.pack()
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready - Load a paper to begin",
            font=('Consolas', 10),
            bg='#0f3460',
            fg='#888888',
            anchor='w',
            padx=10
        )
        self.status_bar.pack(fill='x', side='bottom')
        
        # Keyboard shortcuts
        self.root.bind('r', lambda e: self.mark_red())
        self.root.bind('b', lambda e: self.mark_blue())
        self.root.bind('s', lambda e: self.skip_term())
    
    def load_paper(self):
        """Load a paper for analysis."""
        filepath = filedialog.askopenfilename(
            title="Select Paper",
            initialdir=r"O:\Theophysics_Master\TM SUBSTACK\Logos",
            filetypes=[("Markdown files", "*.md"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        self.current_paper = Path(filepath)
        self.status_bar.config(text=f"Analyzing: {self.current_paper.name}")
        self.root.update()
        
        # Analyze
        self.analysis = self.manager.analyze_paper(self.current_paper)
        self.undecided_terms = self.analysis['undecided']
        self.current_index = 0
        
        # Update stats
        summary = self.analysis['summary']
        stats_text = (
            f"Paper: {self.current_paper.name}\n"
            f"🔴 RED: {summary['red_terms']} terms ({summary['red_percentage']:.1f}%)  |  "
            f"🔵 BLUE: {summary['blue_terms']} terms ({summary['blue_percentage']:.1f}%)  |  "
            f"⚪ UNDECIDED: {summary['undecided_terms']} terms"
        )
        self.stats_label.config(text=stats_text)
        
        if not self.undecided_terms:
            self.term_display.config(text="✅ All terms decided!")
            self.count_display.config(text="")
            self.progress_label.config(text="")
            self.status_bar.config(text="Complete - All terms have been reviewed")
            messagebox.showinfo("Complete", "All terms in this paper have been decided!")
        else:
            # Enable buttons
            self.red_btn.config(state='normal')
            self.blue_btn.config(state='normal')
            self.skip_btn.config(state='normal')
            
            # Show first term
            self.show_current_term()
    
    def show_current_term(self):
        """Display current term."""
        if self.current_index >= len(self.undecided_terms):
            self.term_display.config(text="✅ Review Complete!")
            self.count_display.config(text="")
            self.progress_label.config(text="")
            self.status_bar.config(text="Complete - All undecided terms reviewed")
            self.red_btn.config(state='disabled')
            self.blue_btn.config(state='disabled')
            self.skip_btn.config(state='disabled')
            
            # Offer to reload
            if messagebox.askyesno("Complete", "All undecided terms reviewed! Load another paper?"):
                self.load_paper()
            return
        
        term, count = self.undecided_terms[self.current_index]
        
        self.term_display.config(text=f'"{term}"')
        self.count_display.config(text=f"Appears {count} times in this paper")
        self.progress_label.config(
            text=f"Term {self.current_index + 1} of {len(self.undecided_terms)}"
        )
        self.status_bar.config(text=f"Reviewing: {term}")
    
    def mark_red(self):
        """Mark current term as RED (exclude)."""
        if self.current_index >= len(self.undecided_terms):
            return
        
        term, count = self.undecided_terms[self.current_index]
        self.manager.mark_red(term)
        
        # Flash red
        self.term_display.config(fg='#e94560')
        self.root.after(200, lambda: self.term_display.config(fg='#ffffff'))
        
        # Next term
        self.current_index += 1
        self.root.after(250, self.show_current_term)
    
    def mark_blue(self):
        """Mark current term as BLUE (include)."""
        if self.current_index >= len(self.undecided_terms):
            return
        
        term, count = self.undecided_terms[self.current_index]
        self.manager.mark_blue(term)
        
        # Flash blue
        self.term_display.config(fg='#4ec9b0')
        self.root.after(200, lambda: self.term_display.config(fg='#ffffff'))
        
        # Next term
        self.current_index += 1
        self.root.after(250, self.show_current_term)
    
    def skip_term(self):
        """Skip current term (decide later)."""
        if self.current_index >= len(self.undecided_terms):
            return
        
        # Flash gray
        self.term_display.config(fg='#666666')
        self.root.after(200, lambda: self.term_display.config(fg='#ffffff'))
        
        # Next term
        self.current_index += 1
        self.root.after(250, self.show_current_term)


def main():
    root = tk.Tk()
    app = TermFilterGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
