"""
TTS-Ready Pipeline Tab - Transform Markdown for text-to-speech
"""

import re
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, 
    QLabel, QGroupBox, QCheckBox, QSpinBox, QSplitter
)
from PySide6.QtCore import Qt
from .base import BaseTab
from core.tts_preprocessor import TTSPreprocessor
from core.math_translator import MathTranslator


class TTSTab(BaseTab):
    """Tab for TTS-Ready Pipeline processing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.preprocessor = TTSPreprocessor()
        self.math_translator = MathTranslator()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("🎙️ TTS-Ready Pipeline")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
        
        # Description
        desc = QLabel(
            "Transform Markdown into speech-optimized text. "
            "Removes formatting, handles LaTeX, normalizes structure."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(desc)
        
        # Configuration panel
        config_group = self._create_config_panel()
        layout.addWidget(config_group)
        
        # Splitter for input/output
        splitter = QSplitter(Qt.Vertical)
        
        # Input section
        input_group = QGroupBox("📝 Input (Markdown)")
        input_layout = QVBoxLayout()
        
        self.txt_input = QTextEdit()
        self.txt_input.setPlaceholderText(
            "Paste your Markdown here...\n\n"
            "# Example Heading\n"
            "This is a paragraph with **bold** and *italic*.\n\n"
            "- Bullet point 1\n"
            "- Bullet point 2\n\n"
            "Math: $E = mc^2$\n"
        )
        self.txt_input.setMinimumHeight(250)
        input_layout.addWidget(self.txt_input)
        
        input_group.setLayout(input_layout)
        splitter.addWidget(input_group)
        
        # Output section
        output_group = QGroupBox("🔊 Output (TTS-Ready)")
        output_layout = QVBoxLayout()
        
        self.txt_output = QTextEdit()
        self.txt_output.setReadOnly(True)
        self.txt_output.setPlaceholderText("Processed text will appear here...")
        self.txt_output.setMinimumHeight(200)
        output_layout.addWidget(self.txt_output)
        
        output_group.setLayout(output_layout)
        splitter.addWidget(output_group)
        
        # Set initial sizes (input larger)
        splitter.setSizes([350, 250])
        
        layout.addWidget(splitter)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_add_layer = QPushButton("📝 Add Translation Layer")
        btn_add_layer.clicked.connect(self._add_translation_layer)
        btn_add_layer.setStyleSheet("font-size: 11pt; padding: 8px; background-color: #2a5f8f;")
        btn_add_layer.setToolTip("Keep LaTeX, add English translation below")
        button_layout.addWidget(btn_add_layer)
        
        btn_process = QPushButton("🔊 TTS Mode")
        btn_process.clicked.connect(self._process_text)
        btn_process.setStyleSheet("font-size: 11pt; padding: 8px; background-color: #5f8f2a;")
        btn_process.setToolTip("Replace LaTeX with English for TTS reading")
        button_layout.addWidget(btn_process)
        
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.clicked.connect(self._clear_all)
        button_layout.addWidget(btn_clear)
        
        btn_copy = QPushButton("📋 Copy Output")
        btn_copy.clicked.connect(self._copy_output)
        button_layout.addWidget(btn_copy)
        
        layout.addLayout(button_layout)
        
        # Stats label
        self.lbl_stats = QLabel("")
        self.lbl_stats.setStyleSheet("padding: 5px; color: #666;")
        layout.addWidget(self.lbl_stats)
        
        self.setLayout(layout)
    
    def _create_config_panel(self) -> QGroupBox:
        """Create configuration panel."""
        group = QGroupBox("⚙️ Configuration")
        layout = QVBoxLayout()
        
        # Row 1: LaTeX handling
        row1 = QHBoxLayout()
        
        self.chk_strip_latex = QCheckBox("Strip LaTeX")
        self.chk_strip_latex.setChecked(False)
        self.chk_strip_latex.toggled.connect(self._update_config)
        row1.addWidget(self.chk_strip_latex)
        
        self.chk_verbalize_latex = QCheckBox("Verbalize LaTeX")
        self.chk_verbalize_latex.setChecked(False)
        self.chk_verbalize_latex.toggled.connect(self._update_config)
        row1.addWidget(self.chk_verbalize_latex)
        
        self.chk_translate_math = QCheckBox("📐 Translate Math to English")
        self.chk_translate_math.setChecked(True)
        self.chk_translate_math.setStyleSheet("font-weight: bold;")
        row1.addWidget(self.chk_translate_math)
        
        row1.addStretch()
        layout.addLayout(row1)
        
        # Row 2: Content handling
        row2 = QHBoxLayout()
        
        self.chk_keep_bullets = QCheckBox("Keep Bullets")
        self.chk_keep_bullets.setChecked(True)
        self.chk_keep_bullets.toggled.connect(self._update_config)
        row2.addWidget(self.chk_keep_bullets)
        
        self.chk_expand_acronyms = QCheckBox("Expand Acronyms")
        self.chk_expand_acronyms.setChecked(True)
        self.chk_expand_acronyms.toggled.connect(self._update_config)
        row2.addWidget(self.chk_expand_acronyms)
        
        self.chk_split_sentences = QCheckBox("Split Long Sentences")
        self.chk_split_sentences.setChecked(True)
        self.chk_split_sentences.toggled.connect(self._update_config)
        row2.addWidget(self.chk_split_sentences)
        
        row2.addStretch()
        layout.addLayout(row2)
        
        # Row 3: Sentence length
        row3 = QHBoxLayout()
        
        lbl_max_length = QLabel("Max Sentence Length:")
        row3.addWidget(lbl_max_length)
        
        self.spin_max_length = QSpinBox()
        self.spin_max_length.setMinimum(10)
        self.spin_max_length.setMaximum(100)
        self.spin_max_length.setValue(30)
        self.spin_max_length.setSuffix(" words")
        self.spin_max_length.valueChanged.connect(self._update_config)
        row3.addWidget(self.spin_max_length)
        
        row3.addStretch()
        layout.addLayout(row3)
        
        group.setLayout(layout)
        return group
    
    def _update_config(self):
        """Update preprocessor configuration from UI."""
        config = {
            'strip_latex': self.chk_strip_latex.isChecked(),
            'verbalize_latex': self.chk_verbalize_latex.isChecked(),
            'keep_bullets': self.chk_keep_bullets.isChecked(),
            'expand_acronyms': self.chk_expand_acronyms.isChecked(),
            'split_long_sentences': self.chk_split_sentences.isChecked(),
            'max_sentence_length': self.spin_max_length.value()
        }
        
        # Mutual exclusivity for LaTeX options
        if self.chk_strip_latex.isChecked() and self.chk_verbalize_latex.isChecked():
            # If both checked, uncheck the other
            sender = self.sender()
            if sender == self.chk_strip_latex:
                self.chk_verbalize_latex.setChecked(False)
            else:
                self.chk_strip_latex.setChecked(False)
            
            config['strip_latex'] = self.chk_strip_latex.isChecked()
            config['verbalize_latex'] = self.chk_verbalize_latex.isChecked()
        
        self.preprocessor = TTSPreprocessor(config)
    
    def _add_translation_layer(self):
        """Add English translation layer below LaTeX (keeps LaTeX visible)."""
        input_text = self.txt_input.toPlainText()
        
        if not input_text.strip():
            self.lbl_stats.setText("⚠️ No input text to process")
            return
        
        try:
            # Add translation layers
            output_text = self.math_translator.add_translation_layer(
                input_text,
                level='basic',
                format_style='plain'
            )
            
            self.txt_output.setPlainText(output_text)
            
            # Count LaTeX occurrences
            latex_count = len(re.findall(r'\$[^\$]+\$|\$\$.*?\$\$', input_text, re.DOTALL))
            
            self.lbl_stats.setText(
                f"✅ Added {latex_count} translation layers (LaTeX preserved)"
            )
        except Exception as e:
            self.lbl_stats.setText(f"❌ Error: {str(e)}")
    
    def _process_text(self):
        """Process input text for TTS (replaces LaTeX with English)."""
        input_text = self.txt_input.toPlainText()
        
        if not input_text.strip():
            self.lbl_stats.setText("⚠️ No input text to process")
            return
        
        try:
            # First, translate math if enabled
            if self.chk_translate_math.isChecked():
                output_text = self.math_translator.extract_translations_only(
                    input_text,
                    level='basic'
                )
            else:
                output_text = input_text
            
            # Then process through TTS pipeline
            output_text = self.preprocessor.process(output_text)
            
            self.txt_output.setPlainText(output_text)
            
            # Calculate stats
            input_words = len(input_text.split())
            output_words = len(output_text.split())
            reduction = ((input_words - output_words) / input_words * 100) if input_words > 0 else 0
            
            self.lbl_stats.setText(
                f"✅ TTS Ready: {input_words} → {output_words} words "
                f"({reduction:.1f}% reduction)"
            )
        except Exception as e:
            self.lbl_stats.setText(f"❌ Error: {str(e)}")
    
    def _clear_all(self):
        """Clear both input and output."""
        self.txt_input.clear()
        self.txt_output.clear()
        self.lbl_stats.clear()
    
    def _copy_output(self):
        """Copy output to clipboard."""
        from PySide6.QtWidgets import QApplication
        
        output_text = self.txt_output.toPlainText()
        if output_text:
            QApplication.clipboard().setText(output_text)
            self.lbl_stats.setText("📋 Copied to clipboard!")

