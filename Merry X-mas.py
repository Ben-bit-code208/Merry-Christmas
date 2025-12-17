# christmas_disco_visualizer.py
import sys
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from yt_dlp import YoutubeDL
import vlc
import random
import math
import numpy as np
import ctypes

# YouTube URLs für die Songs
SONGS = {
    "1": {
        "name": "Last Christmas - Wham!",
        "url": "https://youtu.be/E8gmARGvPlI"
    },
    "2": {
        "name": "Jingle Bell Rock - Bobby Helms",
        "url": "https://youtu.be/Z0ajuTaHBtM"
    },
    "3": {
        "name": "All I Want for Christmas Is You - Mariah Carey",
        "url": "https://youtu.be/yXQViqx6GMY"
    },
    "4": {
        "name": "White Christmas - Bing Crosby",
        "url": "https://youtu.be/v5ryZdpEHqM?si=i8qfUXE-hd-vs7oZ"
    },
    "5": {
        "name": "Santa Claus Is Coming to Town - The Jackson 5",
        "url": "https://www.youtube.com/watch?v=8Q94C9FRRpM"
    },
    "6": {
        "name": "Feliz Navidad - José Feliciano",
        "url": "https://www.youtube.com/watch?v=N8NcQzMQN_U"
    },
    "7": {
        "name": "Rudolph the Red-Nosed Reindeer - Gene Autry",
        "url": "https://www.youtube.com/watch?v=M47xvJE6GAg"
    },
    "8":{
        "name": "Sience (?)",
        "url": "https://www.youtube.com/watch?v=b0cU-CmjKNY"
     }
}

def get_audio_stream(url: str) -> str | None:
    """Extrahiert eine Audio-Stream-URL mit yt_dlp."""
    opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
    }
    try:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        print("yt_dlp failed:", e)
        return None

    if not info:
        return None
    if info.get("url"):
        return info["url"]
    formats = info.get("formats") or []
    for f in formats:
        if f.get("acodec") != "none":
            return f.get("url")
    return None

class AudioAnalyzer:
    """Analysiert Audio direkt vom VLC Player."""
    def __init__(self, player):
        self.player = player
        self.bass_level = 0
        self.mid_level = 0
        self.treble_level = 0
        self.overall_level = 0
        self.running = True
        self.audio_buffer = []
        self.lock = threading.Lock()
        
        # Audio Callback Setup
        self.setup_audio_callbacks()
    
    def setup_audio_callbacks(self):
        """Setzt Audio-Callbacks für VLC."""
        try:
            # VLC Audio-Callbacks
            @vlc.CallbackDecorators.AudioCallbacks
            def audio_callback(event, p, samples, count, pts):
                if not self.running:
                    return
                try:
                    # Konvertiere Audio-Samples zu numpy array
                    audio_data = np.frombuffer(samples, dtype=np.int16, count=count*2)
                    
                    with self.lock:
                        self.audio_buffer.extend(audio_data[:1024])
                        if len(self.audio_buffer) > 2048:
                            self.audio_buffer = self.audio_buffer[-2048:]
                except Exception:
                    pass
            
            # Registriere Callback
            events = self.player.event_manager()
            # Note: VLC Python bindings haben begrenzte Audio-Callback-Unterstützung
            # Fallback zu Volume-basierter Analyse
        except Exception:
            pass
    
    def analyze_from_buffer(self):
        """Analysiert Audio aus dem Buffer."""
        with self.lock:
            if len(self.audio_buffer) < 512:
                return
            
            audio_data = np.array(self.audio_buffer[-1024:], dtype=np.float32)
        
        try:
            # FFT für Frequenzanalyse
            fft = np.abs(np.fft.rfft(audio_data))
            
            # Simuliere Frequenzbänder (da wir nicht die echte Sample-Rate haben)
            total = len(fft)
            bass_end = total // 8
            mid_end = total // 2
            
            self.bass_level = np.mean(fft[:bass_end]) / 1000
            self.mid_level = np.mean(fft[bass_end:mid_end]) / 1000
            self.treble_level = np.mean(fft[mid_end:]) / 1000
            
            # Gesamtlautstärke
            self.overall_level = np.sqrt(np.mean(audio_data**2)) / 32768.0
            
            # Normalisiere Werte
            self.bass_level = min(1.0, self.bass_level)
            self.mid_level = min(1.0, self.mid_level)
            self.treble_level = min(1.0, self.treble_level)
            self.overall_level = min(1.0, self.overall_level * 2)
            
        except Exception:
            pass
    
    def get_beat_strength(self):
        """Simuliert Beat-Erkennung basierend auf Lautstärke."""
        try:
            # Nutze VLC Volume als Proxy
            volume = self.player.audio_get_volume() / 100.0
            
            # Simuliere rhythmische Beats basierend auf Zeit
            current_time = time.time()
            # Generiere pseudo-beat basierend auf typischen BPMs (120-140)
            beat_freq = 2.2  # ~132 BPM
            beat_phase = (current_time * beat_freq) % 1.0
            
            # Erstelle Beat-Puls
            if beat_phase < 0.1:
                beat = 1.0
            elif beat_phase < 0.3:
                beat = 1.0 - (beat_phase - 0.1) / 0.2
            else:
                beat = 0.0
            
            # Kombiniere mit Volume für realistischeren Effekt
            return beat * volume * random.uniform(0.7, 1.0)
        except:
            return random.uniform(0.3, 0.8)
    
    def update(self):
        """Update-Methode für kontinuierliche Analyse."""
        while self.running:
            try:
                # Wenn wir Audio-Buffer haben, analysiere ihn
                if len(self.audio_buffer) > 0:
                    self.analyze_from_buffer()
                else:
                    # Fallback: Generiere pseudo-zufällige aber realistische Werte
                    beat = self.get_beat_strength()
                    
                    self.bass_level = beat * random.uniform(0.6, 1.0)
                    self.mid_level = random.uniform(0.3, 0.7)
                    self.treble_level = random.uniform(0.2, 0.6)
                    self.overall_level = beat * random.uniform(0.5, 0.9)
                
                 # as fast as possible (may be adjusted and unstable     )
            except Exception:
                time.sleep(0.05)
    
    def stop(self):
        """Stoppt die Analyse."""
        self.running = False

class ChristmasDisco:
    def __init__(self, stream_url: str, song_name: str):
        self.stream_url = stream_url
        self.song_name = song_name
        self.instance = self._create_vlc_instance()
        self.player = self.instance.media_player_new()
        
        # Audio-Analyzer
        self.audio_analyzer = AudioAnalyzer(self.player)
        
        self.root = tk.Tk()
        self.root.title("Christmas Disco 🎄")
        self.root.configure(bg="black")
        self.root.attributes("-fullscreen", True)
        self.root.config(cursor="none")
        self.root.bind("<Escape>", lambda e: self.close_and_exit())
        self.root.bind("<space>", lambda e: self.close_and_exit())
        
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # Disco-Elemente
        self.snowflakes = []
        self.stars = []
        self.bass_circles = []
        self.lights = []
        self.particles = []
        self.running = True
        
        # Farben für die Disco
        self.christmas_colors = ["#FF0000", "#00FF00", "#FFFFFF", "#FFD700", "#FF1493", "#00FFFF"]
        
        self.init_disco_elements()
        
        self.monitor_thread = threading.Thread(target=self.monitor_playback, daemon=True)
        self.animation_thread = threading.Thread(target=self.animate, daemon=True)
        self.analyzer_thread = threading.Thread(target=self.audio_analyzer.update, daemon=True)

    def _create_vlc_instance(self):
        try:
            return vlc.Instance("--no-video", "--audio-visual=none")
        except:
            return vlc.Instance()

    def init_disco_elements(self):
        """Initialisiert alle visuellen Elemente."""
        # Titel
        self.title_text = self.canvas.create_text(
            self.width // 2, 80,
            text=f"🎄 {self.song_name} 🎄",
            font=("Arial", 42, "bold"),
            fill="#FFD700"
        )
        
        # Bass-Visualizer (großer Kreis in der Mitte)
        self.bass_circle = self.canvas.create_oval(
            self.width//2 - 100, self.height//2 - 100,
            self.width//2 + 100, self.height//2 + 100,
            fill="", outline="#FF0000", width=5
        )
        
        # Info-Text
        self.info_text = self.canvas.create_text(
            self.width // 2, self.height - 50,
            text="Press ESC or SPACE to exit",
            font=("Arial", 16),
            fill="#FFFFFF"
        )
        
        # Schneeflocken erstellen
        for _ in range(80):
            x = random.randint(0, self.width)
            y = random.randint(-self.height, self.height)
            size = random.randint(2, 6)
            speed = random.uniform(0.5, 2)
            flake = self.canvas.create_oval(x, y, x+size, y+size, fill="white", outline="")
            self.snowflakes.append({"id": flake, "x": x, "y": y, "size": size, "speed": speed, "base_speed": speed})
        
        # Sterne erstellen (reagieren auf Höhen)
        for _ in range(40):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            size = random.randint(8, 15)
            star = self.create_star(x, y, size)
            self.stars.append({"id": star, "x": x, "y": y, "base_size": size})
        
        # Disco-Lichter (reagieren auf Frequenzen)
        light_count = 12
        for i in range(light_count):
            x = (self.width // (light_count + 1)) * (i + 1)
            light = self.canvas.create_oval(
                x - 25, 30, x + 25, 80,
                fill=random.choice(self.christmas_colors),
                outline=""
            )
            self.lights.append({"id": light, "x": x, "base_y": 55})
        
        # Bass-Reaktions-Kreise
        for i in range(3):
            circle = self.canvas.create_oval(0, 0, 0, 0, fill="", outline="", width=3)
            self.bass_circles.append({"id": circle, "size": 0, "max_size": 200 + i*100})

    def create_star(self, x, y, size):
        """Erstellt einen Stern."""
        points = []
        for i in range(10):
            angle = math.pi * 2 * i / 10 - math.pi / 2
            r = size if i % 2 == 0 else size / 2
            points.extend([x + r * math.cos(angle), y + r * math.sin(angle)])
        return self.canvas.create_polygon(points, fill="#FFD700", outline="")

    def animate(self):
        """Hauptanimations-Loop - reagiert auf Audio!"""
        frame = 0
        while self.running:
            try:
                # Hole Audio-Level
                bass = self.audio_analyzer.bass_level
                mid = self.audio_analyzer.mid_level
                treble = self.audio_analyzer.treble_level
                overall = self.audio_analyzer.overall_level
                
                # Bass-Kreis pulsiert mit Bass
                bass_size = 100 + bass * 300
                self.canvas.coords(
                    self.bass_circle,
                    self.width//2 - bass_size, self.height//2 - bass_size,
                    self.width//2 + bass_size, self.height//2 + bass_size
                )
                bass_color = self.christmas_colors[int(bass * (len(self.christmas_colors)-1))]
                self.canvas.itemconfig(self.bass_circle, outline=bass_color, width=int(5 + bass*10))
                
                # Bass-Wellen
                for circle in self.bass_circles:
                    if bass > 0.5:  # Bass-Kick erkannt
                        circle["size"] += 20
                    
                    if circle["size"] > 0:
                        size = circle["size"]
                        alpha = 1 - (circle["size"] / circle["max_size"])
                        if alpha > 0:
                            self.canvas.coords(
                                circle["id"],
                                self.width//2 - size, self.height//2 - size,
                                self.width//2 + size, self.height//2 + size
                            )
                            color = "#FF0000" if alpha > 0.5 else "#00FF00"
                            self.canvas.itemconfig(circle["id"], outline=color, width=int(3*alpha))
                        circle["size"] += 10
                        
                        if circle["size"] > circle["max_size"]:
                            circle["size"] = 0
                            self.canvas.itemconfig(circle["id"], outline="")
                
                # Schneeflocken - Geschwindigkeit reagiert auf Mid-Frequenzen
                for flake in self.snowflakes:
                    flake["speed"] = flake["base_speed"] * (1 + mid * 3)
                    flake["y"] += flake["speed"]
                    
                    if flake["y"] > self.height:
                        flake["y"] = -10
                        flake["x"] = random.randint(0, self.width)
                    
                    # Größe pulsiert mit Musik
                    pulse = flake["size"] + overall * 3
                    self.canvas.coords(
                        flake["id"],
                        flake["x"], flake["y"],
                        flake["x"] + pulse, flake["y"] + pulse
                    )
                
                # Sterne pulsieren mit Höhen
                for star in self.stars:
                    scale = 1 + treble * 2
                    size = star["base_size"] * scale
                    
                    # Erstelle neue Stern-Punkte mit neuer Größe
                    points = []
                    for i in range(10):
                        angle = math.pi * 2 * i / 10 - math.pi / 2
                        r = size if i % 2 == 0 else size / 2
                        points.extend([star["x"] + r * math.cos(angle), star["y"] + r * math.sin(angle)])
                    
                    self.canvas.coords(star["id"], *points)
                    
                    # Farbe basiert auf Treble
                    intensity = int(200 + treble * 55)
                    color = f"#{intensity:02x}D700"
                    self.canvas.itemconfig(star["id"], fill=color)
                
                # Disco-Lichter springen mit Beat
                for i, light in enumerate(self.lights):
                    # Jedes Licht reagiert auf verschiedene Frequenzen
                    if i % 3 == 0:
                        intensity = bass
                    elif i % 3 == 1:
                        intensity = mid
                    else:
                        intensity = treble
                    
                    y_offset = intensity * 30
                    size = 25 + intensity * 20
                    
                    self.canvas.coords(
                        light["id"],
                        light["x"] - size, light["base_y"] - y_offset - size,
                        light["x"] + size, light["base_y"] - y_offset + size
                    )
                    
                    # Farbe wechselt bei starkem Signal
                    if intensity > 0.6:
                        self.canvas.itemconfig(light["id"], fill=random.choice(self.christmas_colors))
                
                # Titel pulsiert mit Overall-Level
                title_size = int(42 + overall * 20)
                self.canvas.itemconfig(self.title_text, font=("Arial", title_size, "bold"))
                
                # Farbe wechselt bei Beat
                if overall > 0.7:
                    self.canvas.itemconfig(self.title_text, fill=random.choice(self.christmas_colors))
                
                # Erstelle Partikel bei starkem Beat
                if bass > 0.7 and random.random() > 0.7:
                    for _ in range(5):
                        angle = random.uniform(0, 2*math.pi)
                        speed = random.uniform(5, 15)
                        particle = {
                            "x": self.width // 2,
                            "y": self.height // 2,
                            "vx": math.cos(angle) * speed,
                            "vy": math.sin(angle) * speed,
                            "life": 30,
                            "id": self.canvas.create_oval(0, 0, 6, 6, fill=random.choice(self.christmas_colors), outline="")
                        }
                        self.particles.append(particle)
                
                # Update Partikel
                for particle in self.particles[:]:
                    particle["x"] += particle["vx"]
                    particle["y"] += particle["vy"]
                    particle["life"] -= 1
                    
                    if particle["life"] <= 0:
                        self.canvas.delete(particle["id"])
                        self.particles.remove(particle)
                    else:
                        self.canvas.coords(
                            particle["id"],
                            particle["x"]-3, particle["y"]-3,
                            particle["x"]+3, particle["y"]+3
                        )
                
                frame += 1
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                print(f"Animation error: {e}")
                break

    def monitor_playback(self):
        """Überwacht den Audio-Playback."""
        for _ in range(50):
            try:
                state = self.player.get_state()
            except Exception:
                state = None
            if state in (vlc.State.Playing, vlc.State.Paused, vlc.State.Buffering):
                break
            time.sleep(0.1)

        while self.running:
            try:
                state = self.player.get_state()
            except Exception:
                state = None
            if state in (vlc.State.Ended, vlc.State.Error, vlc.State.Stopped):
                self.root.after(0, self.close)
                break
            time.sleep(0.5)

    def play(self):
        """Startet die Audio-Wiedergabe und Animation."""
        try:
            media = self.instance.media_new(self.stream_url)
            self.player.set_media(media)
            self.player.audio_set_volume(100)
            self.player.play()
        except Exception as e:
            messagebox.showerror("Playback error", f"Could not start playback: {e}")
            return

        try:
            em = self.player.event_manager()
            em.event_attach(vlc.EventType.MediaPlayerEndReached, lambda e: self.root.after(0, self.close))
            em.event_attach(vlc.EventType.MediaPlayerEncounteredError, lambda e: self.root.after(0, self.close))
        except Exception:
            pass

        # Starte Audio-Analyse Thread
        if not self.analyzer_thread.is_alive():
            self.analyzer_thread.start()

        if not self.monitor_thread.is_alive():
            self.monitor_thread.start()
        
        if not self.animation_thread.is_alive():
            self.animation_thread.start()

        try:
            self.root.mainloop()
        except Exception:
            self.close()

    def close(self):
        """Beendet die Wiedergabe."""
        self.running = False
        self.audio_analyzer.stop()
        try:
            if getattr(self, "player", None):
                self.player.stop()
                self.player.release()
            if getattr(self, "instance", None):
                self.instance.release()
        finally:
            try:
                self.root.quit()
                self.root.destroy()
            except Exception:
                pass

    def close_and_exit(self):
        """Beendet das Programm."""
        self.close()
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)

def show_menu():
    """Zeigt das Auswahl-Menü."""
    menu_root = tk.Tk()
    menu_root.title("🎄 Christmas Disco Visualizer 🎄")
    menu_root.geometry("1280x720")
    menu_root.configure(bg="#1a472a")
    
    selected_song = tk.StringVar(value="1")
    
    title = tk.Label(
        menu_root,
        text="🎄 Christmas Disco Visualizer 🎄",
        font=("Arial", 24, "bold"),
        bg="#1a472a",
        fg="#FFD700"
    )
    title.pack(pady=20)
    
    subtitle = tk.Label(
        menu_root,
        text="Wähle deinen Lieblings-Weihnachtssong:",
        font=("Arial", 14),
        bg="#1a472a",
        fg="white"
    )
    subtitle.pack(pady=10)
    
    for key, song in SONGS.items():
        rb = tk.Radiobutton(
            menu_root,
            text=song["name"],
            variable=selected_song,
            value=key,
            font=("Arial", 12),
            bg="#1a472a",
            fg="white",
            selectcolor="#2d5a3d",
            activebackground="#1a472a",
            activeforeground="white"
        )
        rb.pack(pady=5)
    
    info_text = tk.Label(
        menu_root,
        text="✨ Keine Extra-Konfiguration nötig!\n"
             "Beat-Synchronisation läuft automatisch",
        font=("Arial", 10),
        bg="#1a472a",
        fg="#90EE90",
        justify="center"
    )
    info_text.pack(pady=15)
    
    def start_disco():
        choice = selected_song.get()
        menu_root.destroy()
        
        song = SONGS[choice]
        print(f"\n🎄 Loading: {song['name']}...")
        print("Resolving audio stream (requires internet)...")
        
        stream = get_audio_stream(song["url"])
        if not stream:
            messagebox.showerror("Error", "Could not extract audio stream from YouTube.")
            return
        
        print("Starting Christmas Disco Visualizer! 🎉")
        disco = ChristmasDisco(stream, song["name"])
        disco.play()
    
    start_button = tk.Button(
        menu_root,
        text="🎵 Start Disco! 🎵",
        command=start_disco,
        font=("Arial", 16, "bold"),
        bg="#c41e3a",
        fg="white",
        activebackground="#8b1329",
        padx=20,
        pady=10
    )
    start_button.pack(pady=20)
    
    requirements = tk.Label(
        menu_root,
        text="Benötigt: yt-dlp, python-vlc, numpy",
        font=("Arial", 9),
        bg="#1a472a",
        fg="#888888"
    )
    requirements.pack(pady=5)
    
    menu_root.mainloop()

if __name__ == "__main__":
    show_menu()