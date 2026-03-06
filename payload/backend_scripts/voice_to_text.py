"""
Simple Voice-to-Text Recorder
Records audio, transcribes with Whisper, copies to clipboard
Perfect for dictating messages to AI assistants
"""

import os
import sys
import whisper
import sounddevice as sd
import soundfile as sf
import numpy as np
import pyperclip
from datetime import datetime

class VoiceRecorder:
    def __init__(self, model_size="base"):
        """
        Initialize voice recorder with Whisper
        
        Args:
            model_size: tiny, base, small, medium, large
                       (base is good balance of speed/accuracy)
        """
        print("Loading Whisper model...")
        self.model = whisper.load_model(model_size)
        self.sample_rate = 16000
        print(f"✓ Ready! Using '{model_size}' model\n")
    
    def record_audio(self, duration=None):
        """
        Record audio from microphone
        
        Args:
            duration: seconds to record (None = press Enter to stop)
        """
        print("=" * 50)
        if duration:
            print(f"Recording for {duration} seconds...")
            print("Speak now!")
        else:
            print("Recording... Press ENTER to stop")
            print("Speak now!")
        print("=" * 50)
        
        if duration:
            # Fixed duration recording
            audio = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                dtype=np.float32
            )
            sd.wait()
        else:
            # Record until Enter pressed
            recording = []
            
            def callback(indata, frames, time, status):
                recording.append(indata.copy())
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                callback=callback,
                dtype=np.float32
            ):
                input()  # Wait for Enter
            
            audio = np.concatenate(recording, axis=0)
        
        print("✓ Recording complete!\n")
        return audio
    
    def transcribe(self, audio):
        """Transcribe audio to text"""
        print("Transcribing...")
        
        # Save temporary audio file
        temp_file = "temp_recording.wav"
        sf.write(temp_file, audio, self.sample_rate)
        
        # Transcribe
        result = self.model.transcribe(temp_file)
        
        # Clean up
        os.remove(temp_file)
        
        return result["text"].strip()
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        pyperclip.copy(text)
        print("✓ Copied to clipboard!\n")
    
    def run_once(self, duration=None):
        """Record once and transcribe"""
        audio = self.record_audio(duration)
        text = self.transcribe(audio)
        
        print("=" * 50)
        print("TRANSCRIPTION:")
        print("=" * 50)
        print(text)
        print("=" * 50)
        print()
        
        self.copy_to_clipboard(text)
        
        return text
    
    def run_continuous(self):
        """Keep recording until user quits"""
        print("\n" + "=" * 50)
        print("CONTINUOUS MODE")
        print("=" * 50)
        print("Press ENTER to start recording")
        print("Press ENTER again to stop recording")
        print("Type 'quit' to exit")
        print("=" * 50)
        print()
        
        while True:
            command = input("Press ENTER to record (or 'quit' to exit): ").strip().lower()
            
            if command == 'quit':
                print("Goodbye!")
                break
            
            self.run_once()


def main():
    """Main entry point"""
    print("\n" + "=" * 50)
    print("VOICE-TO-TEXT RECORDER")
    print("=" * 50)
    print()
    
    # Choose model size
    print("Choose model size:")
    print("  1. tiny   - Fastest, less accurate")
    print("  2. base   - Good balance (RECOMMENDED)")
    print("  3. small  - Better accuracy, slower")
    print()
    
    choice = input("Enter choice (1-3, default=2): ").strip() or "2"
    
    model_map = {
        "1": "tiny",
        "2": "base",
        "3": "small"
    }
    
    model_size = model_map.get(choice, "base")
    
    # Initialize recorder
    recorder = VoiceRecorder(model_size)
    
    # Choose mode
    print("\nChoose mode:")
    print("  1. Record once")
    print("  2. Continuous (keep recording)")
    print()
    
    mode = input("Enter choice (1-2, default=2): ").strip() or "2"
    
    if mode == "1":
        recorder.run_once()
    else:
        recorder.run_continuous()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped by user. Goodbye!")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have installed:")
        print("  pip install openai-whisper sounddevice soundfile pyperclip")
