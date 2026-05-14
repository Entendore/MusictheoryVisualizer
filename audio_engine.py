import numpy as np
import struct
from PySide6.QtMultimedia import QAudioFormat, QAudioSink
from PySide6.QtCore import QIODevice, QBuffer
from theory import MT

class AudioEngine:
    def __init__(self):
        self.sample_rate = 44100
        self.wave_type = 'Piano'
        self._buffers = []
        
        # Recording state
        self._is_recording = False
        self._rec_chunks = []
        
        fmt = QAudioFormat()
        fmt.setSampleRate(44100); fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.format = fmt
        self.sink = QAudioSink(fmt)
        self.sink.setVolume(0.55)

    def start_recording(self): 
        self._is_recording = True
        self._rec_chunks = []

    def stop_recording(self): 
        self._is_recording = False
        return b''.join(self._rec_chunks)

    def _gen(self, frequencies, duration, volume=0.35):
        n = int(self.sample_rate * duration)
        t = np.linspace(0, duration, n, False)
        sig = np.zeros(n, dtype=np.float64)
        wt = self.wave_type
        
        for f in frequencies:
            if wt == 'Piano':
                sig += np.sin(2*np.pi*f*t) + 0.5*np.sin(4*np.pi*f*t) + 0.25*np.sin(6*np.pi*f*t)
            elif wt == 'Synth':
                sig += np.sin(2*np.pi*f*t) + 0.4*np.sin(2*np.pi*(f*1.005)*t) + 0.4*np.sin(2*np.pi*(f*0.995)*t)
            else: # Sine
                sig += np.sin(2*np.pi*f*t)
                
        mx = np.max(np.abs(sig))
        if mx > 0: sig /= mx
        
        att = min(int(0.01*self.sample_rate), n//4)
        rel = min(int(0.15*self.sample_rate), n//2)
        env = np.ones(n)
        if att > 0: env[:att] = np.linspace(0,1,att)
        if rel > 0 and rel < n: env[-rel:] = np.linspace(1,0,rel)
        
        sig = (sig * env * volume * 32767).astype(np.int16)
        return sig

    def _play_data(self, data):
        # Intercept for recording BEFORE playing to keep A/V sync
        if self._is_recording:
            self._rec_chunks.append(data.tobytes())
            
        buf = QBuffer()
        buf.setData(data.tobytes())
        buf.open(QIODevice.OpenModeFlag.ReadOnly)
        self._buffers.append(buf)
        if len(self._buffers) > 15:
            old = self._buffers.pop(0)
            old.close()
        self.sink.start(buf)

    def play_note(self, midi, dur=0.5, vol=0.35):
        self._play_data(self._gen([MT.midi_to_freq(midi)], dur, vol))

    def play_chord(self, midis, dur=1.0, vol=0.35):
        self._play_data(self._gen([MT.midi_to_freq(m) for m in midis], dur, vol))

    def play_scale(self, midis, note_dur=0.35, gap=0.06, vol=0.35):
        parts = []
        silence = np.zeros(int(self.sample_rate*gap), dtype=np.int16)
        for i, m in enumerate(midis):
            d = self._gen([MT.midi_to_freq(m)], note_dur, vol)
            if i > 0: parts.append(silence)
            parts.append(d)
        self._play_data(np.concatenate(parts))

    def stop(self): 
        self.sink.stop()