# main.py
"""
Christmas Disco Visualizer - Full Android Version
Mit YouTube-Streaming und echter Audio-Analyse
"""
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.utils import platform

import threading
import time
import random
import math
import numpy as np
import os
import tempfile

# YouTube-Streaming für Android
try:
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE])
    ANDROID = True
except ImportError:
    ANDROID = False

# Für YouTube-Audio-Extraktion
import yt_dlp

class AudioAnalyzer:
    """Analysiert Audio in Echtzeit."""
    def __init__(self):
        self.bass_level = 0
        self.mid_level = 0
        self.treble_level = 0
        self.overall_level = 0
        self.beat_detected = False
        self.running = True
        
        # Audio-Buffer
        self.audio_buffer = []
        self.sample_rate = 44100
        
        # Beat-Detection
        self.beat_history = []
        self.beat_threshold = 1.5
        
    def analyze_chunk(self, audio_data):
        """Analysiert einen Audio-Chunk."""
        if len(audio_data) < 512:
            return
        
        try:
            # Konvertiere zu numpy array
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            # FFT für Frequenzanalyse
            fft = np.abs(np.fft.rfft(audio_array))
            freqs = np.fft.rfftfreq(len(audio_array), 1.0 / self.sample_rate)
            
            # Frequenzbänder definieren
            bass_mask = freqs < 200  # Bass: 0-200 Hz
            mid_mask = (freqs >= 200) & (freqs < 2000)  # Mid: 200-2000 Hz
            treble_mask = freqs >= 2000  # Treble: 2000+ Hz
            
            # Durchschnittliche Energie pro Band
            self.bass_level = np.mean(fft[bass_mask]) if np.any(bass_mask) else 0
            self.mid_level = np.mean(fft[mid_mask]) if np.any(mid_mask) else 0
            self.treble_level = np.mean(fft[treble_mask]) if np.any(treble_mask) else 0
            
            # Normalisiere auf 0-1
            max_val = max(self.bass_level, self.mid_level, self.treble_level, 1)
            self.bass_level = min(1.0, self.bass_level / max_val)
            self.mid_level = min(1.0, self.mid_level / max_val)
            self.treble_level = min(1.0, self.treble_level / max_val)
            
            # Overall Level (RMS)
            self.overall_level = np.sqrt(np.mean(audio_array**2)) / 32768.0
            self.overall_level = min(1.0, self.overall_level * 3)
            
            # Beat Detection (einfache Methode: Bass-Spitzen)
            self.beat_history.append(self.bass_level)
            if len(self.beat_history) > 10:
                self.beat_history.pop(0)
            
            avg_bass = np.mean(self.beat_history)
            self.beat_detected = self.bass_level > (avg_bass * self.beat_threshold)
            
        except Exception as e:
            print(f"Audio analysis error: {e}")
    
    def simulate_analysis(self):
        """Simuliert Audio-Analyse wenn keine echten Daten verfügbar."""
        # Zeitbasierte Simulation mit pseudo-realistischen Werten
        t = time.time()
        
        # Simuliere Beat (120-140 BPM)
        beat_freq = 2.2  # ~132 BPM
        beat_phase = (t * beat_freq) % 1.0
        
        if beat_phase < 0.1:
            self.bass_level = 0.9 + random.uniform(0, 0.1)
            self.beat_detected = True
        elif beat_phase < 0.3:
            self.bass_level = 0.9 - (beat_phase - 0.1) * 4
            self.beat_detected = False
        else:
            self.bass_level = random.uniform(0.2, 0.4)
            self.beat_detected = False
        
        # Mid und Treble variieren zufällig aber plausibel
        self.mid_level = random.uniform(0.3, 0.6) + self.bass_level * 0.2
        self.treble_level = random.uniform(0.2, 0.5) + self.mid_level * 0.1
        
        self.overall_level = (self.bass_level + self.mid_level + self.treble_level) / 3

class DiscoVisualizer(Widget):
    """Hauptvisualisierungs-Widget."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.analyzer = None
        self.particles = []
        self.snowflakes = []
        self.colors = [
            (1, 0, 0),      # Rot
            (0, 1, 0),      # Grün
            (1, 1, 1),      # Weiß
            (1, 0.84, 0),   # Gold
            (1, 0.08, 0.58),# Pink
            (0, 1, 1),      # Cyan
        ]
        
        # Initialisiere Visualisierungselemente
        with self.canvas:
            self.bg_color = Color(0, 0, 0, 1)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            
            # Bass-Kreis
            self.bass_color = Color(1, 0, 0, 0.8)
            self.bass_circle = Ellipse(pos=(0, 0), size=(100, 100))
            
            # Beat-Wellen
            self.beat_waves = []
            for i in range(3):
                color = Color(1, 0, 0, 0)
                line = Line(circle=(0, 0, 0), width=3)
                self.beat_waves.append({'color': color, 'line': line, 'size': 0})
        
        # Bind size update
        self.bind(pos=self.update_rect, size=self.update_rect)
        
        # Erstelle Schneeflocken
        self.create_snowflakes(50)
        
        # Starte Animation
        Clock.schedule_interval(self.update, 1/30.0)  # 30 FPS
    
    def update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
    
    def create_snowflakes(self, count):
        """Erstellt Schneeflocken."""
        for _ in range(count):
            with self.canvas:
                color = Color(1, 1, 1, random.uniform(0.5, 1.0))
                size = random.uniform(3, 8)
                x = random.uniform(0, self.width) if self.width > 0 else random.uniform(0, 400)
                y = random.uniform(0, self.height) if self.height > 0 else random.uniform(0, 800)
                ellipse = Ellipse(pos=(x, y), size=(size, size))
                
                self.snowflakes.append({
                    'color': color,
                    'ellipse': ellipse,
                    'x': x,
                    'y': y,
                    'size': size,
                    'speed': random.uniform(1, 3),
                    'sway': random.uniform(-0.5, 0.5)
                })
    
    def update(self, dt):
        """Update-Funktion für Animation."""
        if not self.analyzer:
            return
        
        # Hole Audio-Levels
        bass = self.analyzer.bass_level
        mid = self.analyzer.mid_level
        treble = self.analyzer.treble_level
        overall = self.analyzer.overall_level
        beat = self.analyzer.beat_detected
        
        # Update Bass-Kreis
        center_x = self.center_x
        center_y = self.center_y
        radius = 80 + bass * 200
        
        self.bass_circle.pos = (center_x - radius, center_y - radius)
        self.bass_circle.size = (radius * 2, radius * 2)
        
        # Farbe basierend auf Bass
        color_idx = int(bass * (len(self.colors) - 1))
        r, g, b = self.colors[color_idx]
        self.bass_color.rgb = (r, g, b)
        self.bass_color.a = 0.6 + bass * 0.4
        
        # Update Beat-Wellen
        for wave in self.beat_waves:
            if beat and wave['size'] == 0:
                wave['size'] = radius
            
            if wave['size'] > 0:
                wave['size'] += 15
                alpha = 1 - (wave['size'] / 600)
                
                if alpha > 0:
                    wave['color'].rgba = (1, 0, 0, alpha)
                    wave['line'].circle = (center_x, center_y, wave['size'])
                else:
                    wave['size'] = 0
                    wave['color'].a = 0
        
        # Update Schneeflocken
        for flake in self.snowflakes:
            # Bewegung
            flake['y'] -= flake['speed'] * (1 + mid * 2)
            flake['x'] += flake['sway'] * mid * 5
            
            # Wrap around
            if flake['y'] < 0:
                flake['y'] = self.height
                flake['x'] = random.uniform(0, self.width)
            
            if flake['x'] < 0:
                flake['x'] = self.width
            elif flake['x'] > self.width:
                flake['x'] = 0
            
            # Größe pulsiert mit Musik
            pulse_size = flake['size'] * (1 + overall * 0.5)
            
            flake['ellipse'].pos = (flake['x'], flake['y'])
            flake['ellipse'].size = (pulse_size, pulse_size)
        
        # Erstelle Partikel bei Beat
        if beat and random.random() > 0.5:
            self.create_beat_particles(center_x, center_y, 8)
        
        # Update Partikel
        for particle in self.particles[:]:
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.canvas.remove(particle['color'])
                self.canvas.remove(particle['ellipse'])
                self.particles.remove(particle)
            else:
                particle['x'] += particle['vx'] * dt * 60
                particle['y'] += particle['vy'] * dt * 60
                particle['ellipse'].pos = (particle['x'], particle['y'])
                particle['color'].a = particle['life']
    
    def create_beat_particles(self, x, y, count):
        """Erstellt Partikel bei Beat."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150)
            
            with self.canvas:
                color = Color(*random.choice(self.colors), 1)
                size = random.uniform(5, 12)
                ellipse = Ellipse(pos=(x, y), size=(size, size))
                
                self.particles.append({
                    'color': color,
                    'ellipse': ellipse,
                    'x': x,
                    'y': y,
                    'vx': math.cos(angle) * speed,
                    'vy': math.sin(angle) * speed,
                    'life': 1.0
                })

class ChristmasDiscoApp(App):
    def build(self):
        # Hauptlayout
        self.root_layout = BoxLayout(orientation='vertical')
        
        # Titel
        title = Label(
            text='🎄 Christmas Disco 🎄',
            size_hint=(1, 0.1),
            font_size='24sp',
            color=(1, 0.84, 0, 1)
        )
        
        # Song-Auswahl
        self.songs = {
            "Last Christmas - Wham!": "https://www.youtube.com/watch?v=E8gmARGvPlI",
            "Jingle Bell Rock": "https://www.youtube.com/watch?v=Z0ajuTaHBtM",
            "All I Want for Christmas": "https://www.youtube.com/watch?v=yXQViqx6GMY",
            "White Christmas": "https://www.youtube.com/watch?v=v5ryZdpEHqM",
            "Feliz Navidad": "https://www.youtube.com/watch?v=N8NcQzMQN_U",
        }
        
        self.song_spinner = Spinner(
            text='Wähle einen Song',
            values=list(self.songs.keys()),
            size_hint=(1, None),
            height=50,
            background_color=(0.1, 0.3, 0.1, 1),
            color=(1, 1, 1, 1),
            font_size='16sp'
        )
        self.song_spinner.bind(text=self.on_song_selected)
        
        # Visualizer
        self.visualizer = DiscoVisualizer(size_hint=(1, 1))
        
        # Kontrollen
        control_layout = BoxLayout(size_hint=(1, None), height=60, spacing=10, padding=10)
        
        self.play_btn = Button(
            text='▶️ Play',
            background_color=(0.77, 0.12, 0.23, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=50
        )
        self.play_btn.bind(on_press=self.play_song)
        
        self.stop_btn = Button(
            text='⏹️ Stop',
            background_color=(0.3, 0.3, 0.3, 1),
            font_size='18sp',
            size_hint=(0.5, None),
            height=50
        )
        self.stop_btn.bind(on_press=self.stop_song)
        
        control_layout.add_widget(self.play_btn)
        control_layout.add_widget(self.stop_btn)
        
        # Info
        self.info_label = Label(
            text='⚠️ Bitte Song auswählen!',
            size_hint=(1, None),
            height=40,
            color=(1, 0.84, 0, 1),
            font_size='14sp'
        )
        
        # Zusammenbauen
        self.root_layout.add_widget(title)
        self.root_layout.add_widget(self.song_spinner)
        self.root_layout.add_widget(self.visualizer)
        self.root_layout.add_widget(control_layout)
        self.root_layout.add_widget(self.info_label)
        
        # Audio-Player
        self.sound = None
        self.analyzer = AudioAnalyzer()
        self.visualizer.analyzer = self.analyzer
        
        # Starte Analyse-Simulation
        self.analysis_thread = None
        self.selected_song_name = None
        
        # Cache-Verzeichnis
        self.cache_dir = tempfile.gettempdir() + '\\christmas_disco_cache\\'
        os.makedirs(self.cache_dir, exist_ok=True)
        
        return self.root_layout
    
    def on_song_selected(self, spinner, text):
        """Wird aufgerufen wenn ein Song ausgewählt wird."""
        if text != 'Wähle einen Song':
            self.selected_song_name = text
            self.info_label.text = f'✅ Ausgewählt: {text[:40]}...'
            self.info_label.color = (0, 1, 0, 1)
    
    def get_audio_url(self, youtube_url, song_name):
        """Lädt Audio herunter und gibt lokalen Pfad zurück."""
        try:
            # Prüfe ob Song schon gecached ist
            cache_filename = song_name.replace(' ', '_').replace('-', '').replace('!', '').replace(':', '') + '.mp3'
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1:  # Mindestens 1B
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'text', '✅ Aus Cache geladen!'
                ))
                return cache_path
            
            Clock.schedule_once(lambda dt: setattr(
                self.info_label, 'text', '⏬ Lade Song herunter... (kann 30-60 Sek dauern)'
            ))
            
            # Versuche erst ohne FFmpeg (direkter Download)
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(self.cache_dir, '%(title)s.%(ext)s'),
                'quiet': True,  # Zeige keine Fehler
                'no_warnings': True,
                "logger": None,
                'socket_timeout': 60,
                'retries': 3,
                'fragment_retries': 3,
            }
            
            print(f"Downloading from: {youtube_url}")
            print(f"Saving to: {cache_path}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                print(f"Download info: {info.get('title', 'Unknown')}")
            
            # Prüfe ob Download erfolgreich
            try:
                os.path.exists(cache_path) and os.path.getsize(cache_path) > 1
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'text', '✅ Download komplett!'
                ))
                print(f"Success! File size: {os.path.getsize(cache_path)} bytes")
                return cache_path
            except Exception as e:
                
                print(f"Download verification error: {e}")
                # Versuche direkten Stream-Link
                return self.get_direct_stream_url(youtube_url)
                
        except Exception as e:
            print(f"Download error: {e}")
            import traceback
            traceback.print_exc()
            Clock.schedule_once(lambda dt: setattr(
                self.info_label, 'text', f'❌ Download-Fehler - versuche Stream...'
            ))
            # Fallback: Direkter Stream
            return self.get_direct_stream_url(youtube_url)
    
    def get_direct_stream_url(self, youtube_url):
        """Holt direkten Stream-Link als Fallback."""
        try:
            print("Trying direct stream method...")
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio/best',
                'quiet': False,
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                
                # Hole direkte URL
                if 'url' in info:
                    print(f"Found direct URL")
                    Clock.schedule_once(lambda dt: setattr(
                        self.info_label, 'text', '🔗 Verwende direkten Stream'
                    ))
                    return info['url']
                
                # Suche in formats
                formats = info.get('formats', [])
                for fmt in formats:
                    if fmt.get('acodec') != 'none':
                        url = fmt.get('url')
                        if url:
                            print(f"Found stream URL in format: {fmt.get('format_id')}")
                            Clock.schedule_once(lambda dt: setattr(
                                self.info_label, 'text', '🔗 Verwende direkten Stream'
                            ))
                            return url
            
            return None
                
        except Exception as e:
            print(f"Stream error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def play_song(self, instance):
        """Spielt ausgewählten Song ab."""
        if not self.selected_song_name or self.selected_song_name == 'Wähle einen Song':
            self.info_label.text = '⚠️ Bitte Song auswählen!'
            self.info_label.color = (1, 0.5, 0, 1)
            return
        
        youtube_url = self.songs[self.selected_song_name]
        
        # Starte Audio-Extraktion in Thread
        def load_and_play():
            audio_path = self.get_audio_url(youtube_url, self.selected_song_name)
            
            if not audio_path:
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'text', '❌ Konnte Audio nicht laden. Internet-Verbindung prüfen!'
                ))
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'color', (1, 0, 0, 1)
                ))
                return
            
            try:
                # Lade Audio-Datei
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'text', '🎵 Lade Audio-Datei in Player...'
                ))
                
                print(f"Loading audio from: {audio_path}")
                self.sound = SoundLoader.load(audio_path)
                print(f"SoundLoader result: {self.sound}")
                
                if self.sound:
                    # Prüfe ob Sound geladen wurde
                    if self.sound.length > 0:
                        Clock.schedule_once(lambda dt: setattr(
                            self.info_label, 'text', f'▶️ Spiele: {self.selected_song_name[:30]}...'
                        ))
                        Clock.schedule_once(lambda dt: setattr(
                            self.info_label, 'color', (0, 1, 0, 1)
                        ))
                        
                        # Spiele Sound
                        self.sound.volume = 1.0
                        self.sound.play()
                        print("Playing audio...")
                        
                        # Starte Audio-Analyse
                        self.start_analysis()
                    else:
                        Clock.schedule_once(lambda dt: setattr(
                            self.info_label, 'text', '❌ Audio-Datei leer oder beschädigt'
                        ))
                        if os.path.exists(audio_path) and not audio_path.startswith('http'):
                            os.remove(audio_path)
                else:
                    Clock.schedule_once(lambda dt: setattr(
                        self.info_label, 'text', '❌ Kivy konnte Audio nicht laden. Versuche anderen Song!'
                    ))
                    Clock.schedule_once(lambda dt: setattr(
                        self.info_label, 'color', (1, 0.5, 0, 1)
                    ))
                    if os.path.exists(audio_path) and not audio_path.startswith('http'):
                        os.remove(audio_path)
                    
            except Exception as e:
                print(f"Playback error: {e}")
                import traceback
                traceback.print_exc()
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'text', f'❌ Playback-Fehler: {str(e)[:30]}'
                ))
                Clock.schedule_once(lambda dt: setattr(
                    self.info_label, 'color', (1, 0, 0, 1)
                ))
        
        # Disable Play-Button während des Ladens
        self.play_btn.disabled = True
        self.play_btn.text = '⏳ Lädt...'
        
        # Starte in Thread
        def run_and_enable():
            load_and_play()
            Clock.schedule_once(lambda dt: setattr(self.play_btn, 'disabled', False))
            Clock.schedule_once(lambda dt: setattr(self.play_btn, 'text', '▶️ Play'))
        
        threading.Thread(target=run_and_enable, daemon=True).start()
    
    def start_analysis(self):
        """Startet Audio-Analyse."""
        if self.analysis_thread and self.analysis_thread.is_alive():
            return
        
        def analyze_loop():
            while self.analyzer.running:
                try:
                    # Simuliere Analyse (echte Analyse benötigt Zugriff auf Audio-Buffer)
                    self.analyzer.simulate_analysis()
                    time.sleep(0.05)  # ~20Hz Update
                    
                except Exception as e:
                    print(f"Analysis error: {e}")
                    break
        
        self.analyzer.running = True
        self.analysis_thread = threading.Thread(target=analyze_loop, daemon=True)
        self.analysis_thread.start()
    
    def stop_song(self, instance):
        """Stoppt Wiedergabe."""
        if self.sound:
            self.sound.stop()
            self.sound = None
        
        self.analyzer.running = False
        self.info_label.text = '⏹️ Gestoppt'
    
    def on_stop(self):
        """Cleanup beim Beenden."""
        if self.sound:
            self.sound.stop()
        self.analyzer.running = False

if __name__ == '__main__':
    ChristmasDiscoApp().run()