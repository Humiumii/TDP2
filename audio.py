import threading

# --- Intento 1: pygame (soporta mp3 y loops=-1 nativamente) ---
try:
    import pygame
    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.mixer.init()

    _channels = []

    def start_instance(name: str, loops: int = 0):
        try:
            sound = pygame.mixer.Sound(name)
            ch = sound.play(loops=loops)
            if ch:
                _channels.append(ch)
        except Exception as e:
            print(f"[audio.pygame] error: {e}")

    def stop_one_instance():
        if _channels:
            _channels.pop().stop()

    def stop_all_instances():
        while _channels:
            stop_one_instance()

# --- Intento 2: simpleaudio con looping vía thread ---
except Exception:
    try:
        import os
        import math
        import struct
        import wave
        import simpleaudio as sa

        AUDIO_DIR = os.path.dirname(__file__)
        _loop_events = []
        _play_objs = []

        def _ensure_wav(name: str) -> str:
            base, _ = os.path.splitext(name)
            wav_path = os.path.join(AUDIO_DIR, base + '.wav')
            if os.path.exists(wav_path):
                return wav_path
            framerate, duration, freq = 44100, 0.5, 440.0
            nframes = int(duration * framerate)
            with wave.open(wav_path, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(framerate)
                for i in range(nframes):
                    v = int(32767 * math.sin(2.0 * math.pi * freq * i / framerate))
                    wf.writeframesraw(struct.pack('<h', v))
            return wav_path

        def _loop_player(wave_obj, stop_evt):
            while not stop_evt.is_set():
                play_obj = wave_obj.play()
                while play_obj.is_playing():
                    if stop_evt.is_set():
                        play_obj.stop()
                        return
                    threading.Event().wait(0.05)

        def start_instance(name: str, loops: int = 0):
            try:
                wav = _ensure_wav(name)
                wave_obj = sa.WaveObject.from_wave_file(wav)
                if loops == -1:
                    stop_evt = threading.Event()
                    _loop_events.append(stop_evt)
                    threading.Thread(target=_loop_player, args=(wave_obj, stop_evt), daemon=True).start()
                else:
                    play_obj = wave_obj.play()
                    _play_objs.append(play_obj)
            except Exception as e:
                print(f"[audio.simpleaudio] error: {e}")

        def stop_one_instance():
            if _loop_events:
                _loop_events.pop().set()
            elif _play_objs:
                try:
                    _play_objs.pop().stop()
                except Exception:
                    pass

        def stop_all_instances():
            for evt in _loop_events:
                evt.set()
            _loop_events.clear()
            for p in _play_objs:
                try:
                    p.stop()
                except Exception:
                    pass
            _play_objs.clear()

    # --- Fallback: solo imprime ---
    except Exception:
        _dummy = []

        def start_instance(name: str, loops: int = 0):
            print(f"[audio] start {name} loops={loops}")

        def stop_one_instance():
            print("[audio] stop one")

        def stop_all_instances():
            print("[audio] stop all")
