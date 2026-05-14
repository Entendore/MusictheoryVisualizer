#!/usr/bin/env python3
"""
Music Theory Visualizer for YouTube — Full Recording Edition
PySide6 + NumPy | Record button captures animation + audio → MP4

Recording Workflow:
  1. Click ⏺ Record → choose output .mp4 path
  2. Animation plays automatically while frames + audio are captured
  3. Recording stops when animation ends (or click ■ Stop)
  4. FFmpeg auto-encodes frames+audio into MP4
  5. If FFmpeg missing → frames + WAV + batch script saved instead
"""

import sys, math, os, time, struct, wave, subprocess, shutil, tempfile
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QSpinBox, QTabWidget, QSplitter,
    QCheckBox, QFileDialog, QMessageBox, QSizePolicy, QLineEdit, QProgressBar,
    QProgressDialog, QStatusBar
)
from PySide6.QtCore import (
    Qt, QTimer, QRect, QRectF, QPointF, QSize, Signal, Slot,
    QBuffer, QIODevice
)
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPainterPath,
    QLinearGradient, QRadialGradient, QShortcut, QKeySequence
)
from PySide6.QtMultimedia import QAudioFormat, QAudioSink

# ═══════════════════════════════════════════════════════════════
#  THEME MANAGER
# ═══════════════════════════════════════════════════════════════
class ThemeManager:
    THEMES = {
        'Neon': dict(bg_dark='#0f0f1a', bg_surface='#161625', bg_panel='#1c1c30', accent_blue='#53d8fb', accent_red='#e94560', accent_gold='#ffd93d', accent_green='#6bcb77', accent_purple='#b06cff', accent_orange='#ff8c42', text_light='#eaeaea', text_dim='#888899', piano_white='#f0f0f0', piano_black='#1a1a1a', wood='#6B4F2A', fret='#d0d0d0', string='#c0c0c0'),
        'Midnight': dict(bg_dark='#050510', bg_surface='#0a0a18', bg_panel='#101025', accent_blue='#4488ff', accent_red='#ff4466', accent_gold='#ffcc33', accent_green='#44dd88', accent_purple='#8855ff', accent_orange='#ff7744', text_light='#d0d8f0', text_dim='#556688', piano_white='#e8e8f0', piano_black='#0a0a15', wood='#3E2F1C', fret='#808080', string='#909090'),
        'Sunset': dict(bg_dark='#1a0f0f', bg_surface='#251616', bg_panel='#301c1c', accent_blue='#66bbee', accent_red='#ff6655', accent_gold='#ffaa33', accent_green='#55cc77', accent_purple='#cc66ff', accent_orange='#ff8833', text_light='#f0e8e8', text_dim='#997777', piano_white='#f8f0f0', piano_black='#1a1010', wood='#5C3A1E', fret='#d0b090', string='#e0c0a0'),
        'Ocean': dict(bg_dark='#0a1520', bg_surface='#0f1d2a', bg_panel='#152535', accent_blue='#44ccee', accent_red='#ee5566', accent_gold='#eebb44', accent_green='#44cc88', accent_purple='#8866ee', accent_orange='#ee8844', text_light='#e0eef8', text_dim='#6688aa', piano_white='#eef5fa', piano_black='#0a1520', wood='#2F4F4F', fret='#90a0b0', string='#a0b0c0'),
        'Pastel': dict(bg_dark='#1a1520', bg_surface='#231e2a', bg_panel='#2d2635', accent_blue='#7ec8e3', accent_red='#e88d8d', accent_gold='#f5d78e', accent_green='#8dd3a5', accent_purple='#c49de0', accent_orange='#f0b38a', text_light='#e8e0f0', text_dim='#9988aa', piano_white='#f5f0fa', piano_black='#252030', wood='#5A4F37', fret='#b0a090', string='#c0b0a0'),
    }
    def __init__(self): self._t = dict(self.THEMES['Neon']); self._name = 'Neon'
    def apply(self, name):
        if name in self.THEMES: self._t = dict(self.THEMES[name]); self._name = name
    def __getattr__(self, k):
        if k.startswith('_'): return super().__getattribute__(k)
        return self._t.get(k, '#ffffff')
    @property
    def name(self): return self._name
    @property
    def names(self): return list(self.THEMES.keys())

theme = ThemeManager()

# ═══════════════════════════════════════════════════════════════
#  MUSIC THEORY DATA
# ═══════════════════════════════════════════════════════════════
class MT:
    NOTES = ['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B']
    SCALE_DEGREES = {
        'Major':['1','2','3','4','5','6','7'], 'Natural Minor':['1','2','♭3','4','5','♭6','♭7'],
        'Harmonic Minor':['1','2','♭3','4','5','♭6','7'], 'Melodic Minor':['1','2','♭3','4','5','6','7'],
        'Dorian':['1','2','♭3','4','5','6','♭7'], 'Phrygian':['1','♭2','♭3','4','5','♭6','♭7'],
        'Lydian':['1','2','3','♯4','5','6','7'], 'Mixolydian':['1','2','3','4','5','6','♭7'],
        'Pentatonic Major':['1','2','3','5','6'], 'Blues':['1','♭3','4','♭5','5','♭7'],
    }
    SCALES = {
        'Major': [0,2,4,5,7,9,11], 'Natural Minor': [0,2,3,5,7,8,10],
        'Harmonic Minor': [0,2,3,5,7,8,11], 'Melodic Minor': [0,2,3,5,7,9,11],
        'Dorian': [0,2,3,5,7,9,10], 'Phrygian': [0,1,3,5,7,8,10],
        'Lydian': [0,2,4,6,7,9,11], 'Mixolydian': [0,2,4,5,7,9,10],
        'Pentatonic Major': [0,2,4,7,9], 'Blues': [0,3,5,6,7,10],
    }
    CHORD_TYPES = {
        'Major': [0,4,7], 'Minor': [0,3,7], 'Diminished': [0,3,6],
        'Augmented': [0,4,8], 'Sus2': [0,2,7], 'Sus4': [0,5,7],
        'Major 7th': [0,4,7,11], 'Minor 7th': [0,3,7,10], 'Dominant 7th': [0,4,7,10],
    }
    CHORD_SYMBOLS = {'Major':'', 'Minor':'m', 'Diminished':'dim', 'Augmented':'aug', 'Sus2':'sus2', 'Sus4':'sus4', 'Major 7th':'maj7', 'Minor 7th':'m7', 'Dominant 7th':'7'}
    INTERVALS = ['Unison','m2','M2','m3','M3','P4','Tritone','P5','m6','M6','m7','M7']
    PROGRESSIONS = {
        'I - IV - V - I': [0,5,7,0], 'I - vi - IV - V': [0,9,5,7],
        'I - V - vi - IV': [0,7,9,5], 'ii - V - I - I': [2,7,0,0],
        '12-Bar Blues': [0,0,0,0,5,5,0,0,7,5,0,7],
    }
    CIRCLE = [0,7,2,9,4,11,6,1,8,3,10,5]
    KEY_SIG = {0:0, 7:1, 2:2, 9:3, 4:4, 11:5, 6:6, 5:-1, 10:-2, 3:-3, 8:-4, 1:-5}

    @staticmethod
    def midi_to_freq(m): return 440.0*(2.0**((m-69)/12.0))
    @staticmethod
    def get_scale_notes(r, s): return [(r+i)%12 for i in MT.SCALES[s]]
    @staticmethod
    def get_chord_notes(r, c): return [(r+i)%12 for i in MT.CHORD_TYPES[c]]
    @staticmethod
    def chord_symbol(r, q): return MT.NOTES[r] + MT.CHORD_SYMBOLS.get(q, '')
    @staticmethod
    def key_signature(r): return MT.KEY_SIG.get(r, 0)
    @staticmethod
    def scale_formula(s):
        iv = MT.SCALES[s]; steps = []
        for i in range(len(iv)-1):
            d = iv[i+1]-iv[i]; steps.append('W' if d==2 else 'H' if d==1 else str(d))
        last = 12-iv[-1]; steps.append('W' if last==2 else 'H' if last==1 else str(last))
        return steps
    @staticmethod
    def get_diatonic_chords(root, scale='Major'):
        iv = MT.SCALES[scale]; chords = []; rn = ['I','II','III','IV','V','VI','VII']
        for i, interval in enumerate(iv):
            cr = (root+interval)%12
            third = (iv[(i+2)%len(iv)]-interval)%12; fifth = (iv[(i+4)%len(iv)]-interval)%12
            if third==4 and fifth==7: q='Major'
            elif third==3 and fifth==7: q='Minor'
            elif third==3 and fifth==6: q='Diminished'
            elif third==4 and fifth==8: q='Augmented'
            else: q='Major'
            r = rn[i]
            if q=='Minor': r=r.lower()
            elif q=='Diminished': r=r.lower()+'°'
            chords.append({'root':cr,'quality':q,'roman':r,'notes':MT.get_chord_notes(cr,q),'symbol':MT.chord_symbol(cr,q)})
        return chords


# ═══════════════════════════════════════════════════════════════
#  AUDIO ENGINE (Enhanced with Recording Buffer)
# ═══════════════════════════════════════════════════════════════
class AudioEngine:
    def __init__(self):
        self.sample_rate = 44100; self.wave_type = 'Piano'; self._buffers = []
        self._is_recording = False; self._rec_chunks = []
        fmt = QAudioFormat()
        fmt.setSampleRate(44100); fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        self.format = fmt; self.sink = QAudioSink(fmt); self.sink.setVolume(0.55)

    def start_recording(self): self._is_recording = True; self._rec_chunks = []
    def stop_recording(self): self._is_recording = False; return b''.join(self._rec_chunks)

    def _gen(self, frequencies, duration, volume=0.35):
        n = int(self.sample_rate*duration); t = np.linspace(0, duration, n, False)
        sig = np.zeros(n, dtype=np.float64); wt = self.wave_type
        for f in frequencies:
            if wt == 'Piano':
                sig += np.sin(2*np.pi*f*t) + 0.5*np.sin(4*np.pi*f*t) + 0.25*np.sin(6*np.pi*f*t)
            elif wt == 'Synth':
                sig += np.sin(2*np.pi*f*t) + 0.4*np.sin(2*np.pi*(f*1.005)*t) + 0.4*np.sin(2*np.pi*(f*0.995)*t)
            else: # Sine
                sig += np.sin(2*np.pi*f*t)
        mx = np.max(np.abs(sig))
        if mx > 0: sig /= mx
        att = min(int(0.01*self.sample_rate), n//4); rel = min(int(0.15*self.sample_rate), n//2)
        env = np.ones(n)
        if att > 0: env[:att] = np.linspace(0,1,att)
        if rel > 0 and rel < n: env[-rel:] = np.linspace(1,0,rel)
        sig = (sig * env * volume * 32767).astype(np.int16)
        if self._is_recording: self._rec_chunks.append(sig.tobytes())
        return sig

    def _play_data(self, data):
        buf = QBuffer(); buf.setData(data.tobytes()); buf.open(QIODevice.OpenModeFlag.ReadOnly)
        self._buffers.append(buf)
        if len(self._buffers)>15: old=self._buffers.pop(0); old.close()
        self.sink.start(buf)

    def play_note(self, midi, dur=0.5, vol=0.35):
        self._play_data(self._gen([MT.midi_to_freq(midi)], dur, vol))

    def play_chord(self, midis, dur=1.0, vol=0.35):
        self._play_data(self._gen([MT.midi_to_freq(m) for m in midis], dur, vol))

    def play_scale(self, midis, note_dur=0.35, gap=0.06, vol=0.35):
        parts = []; silence = np.zeros(int(self.sample_rate*gap), dtype=np.int16)
        for i,m in enumerate(midis):
            d = self._gen([MT.midi_to_freq(m)], note_dur, vol)
            if i>0: parts.append(silence)
            parts.append(d)
        self._play_data(np.concatenate(parts))

    def stop(self): self.sink.stop()


# ═══════════════════════════════════════════════════════════════
#  VIDEO RECORDER (Frames + Audio → MP4)
# ═══════════════════════════════════════════════════════════════
class VideoRecorder:
    def __init__(self, widget, audio_engine):
        self.widget = widget; self.audio = audio_engine
        self.timer = QTimer(); self.timer.timeout.connect(self._capture_frame)
        self.is_recording = False; self.frames = []; self.fps = 30
        self.output_path = ''; self.temp_dir = ''

    def start(self, output_path):
        self.output_path = output_path
        self.temp_dir = tempfile.mkdtemp(prefix='mtv_rec_')
        self.frames = []; self.is_recording = True
        self.audio.start_recording()
        self.timer.start(int(1000/self.fps))

    def stop_and_encode(self):
        self.timer.stop(); self.is_recording = False
        raw_audio = self.audio.stop_recording()
        self.widget.statusBar().showMessage("Encoding video... Please wait.")

        # 1. Save Audio
        wav_path = os.path.join(self.temp_dir, 'audio.wav')
        with wave.open(wav_path, 'w') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(44100)
            wf.writeframes(raw_audio)

        # 2. Save Frames (already saved in _capture_frame)

        # 3. Encode with FFmpeg
        ffmpeg_exe = 'ffmpeg'
        if sys.platform == 'win32': ffmpeg_exe = 'ffmpeg.exe'
        
        has_ffmpeg = shutil.which(ffmpeg_exe) is not None

        if has_ffmpeg:
            cmd = [
                ffmpeg_exe, '-y',
                '-framerate', str(self.fps),
                '-i', os.path.join(self.temp_dir, 'frame_%05d.png'),
                '-i', wav_path,
                '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-preset', 'fast',
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', self.output_path
            ]
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                QMessageBox.information(self.widget, "Recording Complete", f"Video saved to:\n{self.output_path}")
                shutil.rmtree(self.temp_dir) # Cleanup
                self.widget.statusBar().showMessage("Ready")
                return True
            except Exception as e:
                QMessageBox.warning(self.widget, "Encoding Failed", f"FFmpeg failed: {e}\n\nSaving raw files instead.")
        else:
            msg = "FFmpeg not found! Cannot auto-encode.\n\n"
        
        # Fallback: Save script and raw files
        fallback_dir = os.path.splitext(self.output_path)[0] + "_raw_frames"
        shutil.move(self.temp_dir, fallback_dir)
        wav_path_new = os.path.join(fallback_dir, 'audio.wav')
        
        script_path = os.path.join(fallback_dir, 'encode.bat' if sys.platform == 'win32' else 'encode.sh')
        with open(script_path, 'w') as f:
            f.write(f"{ffmpeg_exe} -y -framerate {self.fps} -i frame_%05d.png -i audio.wav -c:v libx264 -pix_fmt yuv420p -c:a aac -shortest \"{os.path.abspath(self.output_path)}\"\n")
        
        QMessageBox.information(self.widget, "Raw Files Saved", f"Frames and audio saved to:\n{fallback_dir}\n\nRun the script inside to encode!")
        self.widget.statusBar().showMessage("Ready")
        return False

    def _capture_frame(self):
        if not self.is_recording: return
        idx = len(self.frames)
        path = os.path.join(self.temp_dir, f"frame_{idx:05d}.png")
        pixmap = self.widget.grab()
        pixmap.save(path)
        self.frames.append(path)


# ═══════════════════════════════════════════════════════════════
#  PIANO KEYBOARD
# ═══════════════════════════════════════════════════════════════
class PianoKeyboard(QWidget):
    note_clicked = Signal(int)
    W_IDX = [0,2,4,5,7,9,11]; B_IDX = [1,3,6,8,10]; B_AFTER = {1:0, 3:1, 6:3, 8:4, 10:5}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.start_octave=3; self.num_octaves=3; self.start_midi=(self.start_octave+1)*12
        self.highlighted=set(); self.root_class=None; self.anim_note=None
        self.show_names=True; self.show_degrees=False; self.glow_enabled=True
        self._degree_map={}; self.setMinimumHeight(140); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_highlighted(self, nc, root=None):
        self.highlighted.clear()
        for o in range(self.start_octave, self.start_octave+self.num_octaves):
            for n in nc: self.highlighted.add((o+1)*12+n)
        self.root_class=root; self.update()

    def set_degree_map(self, r, s):
        self._degree_map={}
        iv=MT.SCALES.get(s,[]); dg=MT.SCALE_DEGREES.get(s,[])
        for i, interval in enumerate(iv):
            if i<len(dg): self._degree_map[(r+interval)%12]=dg[i]

    def _geom(self):
        tw=self.num_octaves*7; wkw=self.width()/tw; wkh=self.height()
        return tw, wkw, wkh, wkw*0.58, wkh*0.62

    def _bx(self, n, o, wkw):
        wi=self.B_AFTER.get(n)
        return (o*7+wi+1)*wkw - wkw*0.30 if wi is not None else None

    def _kcol(self, midi, black):
        if midi not in self.highlighted: return QColor(theme.piano_black) if black else QColor(theme.piano_white)
        nc=midi%12
        if self.anim_note==midi: c=QColor(theme.accent_gold)
        elif self.root_class is not None and nc==self.root_class: c=QColor(theme.accent_red)
        else: c=QColor(theme.accent_blue)
        return c.darker(160) if black else c

    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        tw, wkw, wkh, bkw, bkh = self._geom()
        p.fillRect(self.rect(), QColor(theme.bg_dark))

        if self.glow_enabled:
            for o in range(self.num_octaves):
                for i, ni in enumerate(self.W_IDX):
                    midi=self.start_midi+o*12+ni
                    if midi in self.highlighted:
                        x=(o*7+i)*wkw+wkw/2; col=self._kcol(midi, False)
                        grad=QRadialGradient(x, wkh*0.7, wkw*1.2)
                        gc=QColor(col); gc.setAlpha(60)
                        grad.setColorAt(0, gc); grad.setColorAt(1, QColor(0,0,0,0))
                        p.setBrush(QBrush(grad)); p.setPen(Qt.NoPen)
                        p.drawEllipse(QPointF(x, wkh*0.7), wkw*1.2, wkw*0.8)

        for o in range(self.num_octaves):
            for i, ni in enumerate(self.W_IDX):
                midi=self.start_midi+o*12+ni; x=(o*7+i)*wkw; col=self._kcol(midi, False)
                grad=QLinearGradient(x,0,x,wkh); grad.setColorAt(0, col.lighter(110)); grad.setColorAt(1, col)
                p.setPen(QPen(QColor(120,120,130),1)); p.setBrush(QBrush(grad))
                p.drawRoundedRect(QRectF(x+0.5,0,wkw-1,wkh-1),1,3)
                if self.show_names and midi in self.highlighted:
                    nc=midi%12; is_root=self.root_class is not None and nc==self.root_class
                    txt=self._degree_map.get(nc, MT.NOTES[nc]) if self.show_degrees else MT.NOTES[nc]
                    p.setPen(QPen(QColor(20,20,30) if col.lightness()>150 else QColor(255,255,255)))
                    p.setFont(QFont('Segoe UI', max(7,int(wkw*0.26)), QFont.Bold if is_root else QFont.Normal))
                    p.drawText(QRectF(x,wkh-22,wkw,18), Qt.AlignCenter, txt)

        for o in range(self.num_octaves):
            for ni in self.B_IDX:
                midi=self.start_midi+o*12+ni; bx=self._bx(ni,o,wkw)
                if bx is None: continue
                col=self._kcol(midi, True)
                grad=QLinearGradient(bx,0,bx,bkh); grad.setColorAt(0, col.lighter(120)); grad.setColorAt(1, col.darker(140))
                p.setPen(QPen(QColor(5,5,5),1)); p.setBrush(QBrush(grad))
                p.drawRoundedRect(QRectF(bx,0,bkw,bkh),2,5)
                if self.show_names and midi in self.highlighted:
                    nc=midi%12; txt=self._degree_map.get(nc, MT.NOTES[nc]) if self.show_degrees else MT.NOTES[nc]
                    p.setPen(QPen(QColor(240,240,240))); p.setFont(QFont('Segoe UI', max(6,int(bkw*0.30)), QFont.Bold))
                    p.drawText(QRectF(bx,bkh-17,bkw,14), Qt.AlignCenter, txt)
        p.end()

    def mousePressEvent(self, e):
        m=self._midi_at(e.position())
        if m is not None: self.note_clicked.emit(m)

    def _midi_at(self, pos):
        tw, wkw, wkh, bkw, bkh = self._geom(); x,y=pos.x(),pos.y()
        if y<bkh:
            for o in range(self.num_octaves):
                for ni in self.B_IDX:
                    bx=self._bx(ni,o,wkw)
                    if bx is not None and bx<=x<=bx+bkw: return self.start_midi+o*12+ni
        if y<wkh:
            wi=int(x/wkw); o, ki=wi//7, wi%7
            if o<self.num_octaves and ki<7: return self.start_midi+o*12+self.W_IDX[ki]
        return None


# ═══════════════════════════════════════════════════════════════
#  GUITAR FRETBOARD
# ═══════════════════════════════════════════════════════════════
class GuitarFretboard(QWidget):
    TUNING=[40,45,50,55,59,64]; SNAMES=['E','A','D','G','B','e']
    MARKERS=[3,5,7,9,12,15,17,19,21]; DMARKS=[12]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted=set(); self.root_class=None; self.num_frets=21
        self.show_degrees=False; self._degree_map={}
        self.setMinimumHeight(110); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_highlighted(self, nc, root=None):
        self.highlighted=set(nc); self.root_class=root; self.update()
    def set_degree_map(self, r, s):
        self._degree_map={}; iv=MT.SCALES.get(s,[]); dg=MT.SCALE_DEGREES.get(s,[])
        for i, interval in enumerate(iv):
            if i<len(dg): self._degree_map[(r+interval)%12]=dg[i]

    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); ml,mr,mt,mb=28,10,20,12; fw=w-ml-mr; fh=h-mt-mb
        p.fillRect(self.rect(), QColor(theme.bg_surface))
        p.fillRect(QRectF(ml,mt,fw,fh), QColor(theme.wood))
        fp=[ml]
        for f in range(1, self.num_frets+1): fp.append(ml+(f/self.num_frets)*fw)
        for f in self.MARKERS:
            if f>self.num_frets: continue
            cx=(fp[f-1]+fp[f])/2; cy=mt+fh/2
            p.setBrush(QBrush(QColor(255,255,255,45))); p.setPen(Qt.NoPen)
            if f in self.DMARKS:
                p.drawEllipse(QPointF(cx,cy-fh*0.18),4,4); p.drawEllipse(QPointF(cx,cy+fh*0.18),4,4)
            else: p.drawEllipse(QPointF(cx,cy),4,4)
        p.setPen(QPen(QColor(theme.fret),2))
        for f in range(1, self.num_frets+1): p.drawLine(QPointF(fp[f],mt), QPointF(fp[f],mt+fh))
        p.setPen(QPen(QColor(255,255,255,200),3)); p.drawLine(QPointF(ml,mt), QPointF(ml,mt+fh))
        ss=fh/5
        for s in range(6):
            y=mt+s*ss; thick=1.0+(5-s)*0.25; p.setPen(QPen(QColor(theme.string),thick))
            p.drawLine(QPointF(ml,y), QPointF(ml+fw,y))
        for s in range(6):
            base=self.TUNING[s]
            for f in range(self.num_frets+1):
                midi=base+f; nc=midi%12
                if nc not in self.highlighted: continue
                cx=(fp[f-1]+fp[f])/2 if f>0 else ml*0.5+5; cy=mt+s*ss; r=9
                color=QColor(theme.accent_red) if self.root_class is not None and nc==self.root_class else QColor(theme.accent_blue)
                gr=QRadialGradient(cx,cy,r*2); gc=QColor(color); gc.setAlpha(50)
                gr.setColorAt(0,gc); gr.setColorAt(1,QColor(0,0,0,0))
                p.setBrush(QBrush(gr)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(cx,cy),r*2,r*1.5)
                p.setBrush(QBrush(color)); p.setPen(QPen(color.darker(130),1)); p.drawEllipse(QPointF(cx,cy),r,r)
                txt=self._degree_map.get(nc, MT.NOTES[nc]) if self.show_degrees else MT.NOTES[nc]
                p.setPen(QPen(QColor('#ffffff'))); p.setFont(QFont('Segoe UI',6,QFont.Bold))
                p.drawText(QRectF(cx-r,cy-r,2*r,2*r), Qt.AlignCenter, txt)
        p.setPen(QPen(QColor(theme.text_dim))); p.setFont(QFont('Segoe UI',7))
        for s in range(6): p.drawText(QRectF(0,mt+s*ss-7,ml-4,14), Qt.AlignRight|Qt.AlignVCenter, self.SNAMES[s])
        p.end()


# ═══════════════════════════════════════════════════════════════
#  CIRCLE OF FIFTHS
# ═══════════════════════════════════════════════════════════════
class CircleOfFifths(QWidget):
    key_clicked = Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root=0; self.scale_notes=[]; self.diatonic=[]
        self.setMinimumSize(260,260); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_data(self, r, sn, dc): self.root=r; self.scale_notes=sn; self.diatonic=dc; self.update()

    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); cx,cy=w/2,h/2; outer_r=min(w,h)*0.42; inner_r=outer_r*0.60
        grad=QRadialGradient(cx,cy,outer_r*1.15); grad.setColorAt(0,QColor(theme.bg_surface)); grad.setColorAt(1,QColor(theme.bg_dark))
        p.setBrush(QBrush(grad)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(cx,cy),outer_r+22,outer_r+22)
        
        for i, nc in enumerate(MT.CIRCLE):
            angle=math.radians(i*30-90); x=cx+outer_r*math.cos(angle); y=cy+outer_r*math.sin(angle)
            is_root=(nc==self.root); in_scale=nc in self.scale_notes
            quality=''
            for dc in self.diatonic:
                if dc['root']==nc: quality=dc['quality']; break
            r=20
            if is_root:
                gr=QRadialGradient(x,y,r*2); gc=QColor(theme.accent_red); gc.setAlpha(50)
                gr.setColorAt(0,gc); gr.setColorAt(1,QColor(0,0,0,0))
                p.setBrush(QBrush(gr)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(x,y),r*2,r*2)
                p.setBrush(QBrush(QColor(theme.accent_red))); p.setPen(QPen(QColor(theme.accent_red).lighter(150),2))
            elif in_scale:
                c=QColor(theme.accent_blue)
                if quality=='Minor': c=QColor(theme.accent_green)
                elif quality=='Diminished': c=QColor(theme.accent_purple)
                gr=QRadialGradient(x,y,r*1.6); gc2=QColor(c); gc2.setAlpha(30)
                gr.setColorAt(0,gc2); gr.setColorAt(1,QColor(0,0,0,0))
                p.setBrush(QBrush(gr)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(x,y),r*1.6,r*1.6)
                p.setBrush(QBrush(c.darker(150))); p.setPen(QPen(c.lighter(120),2))
            else:
                p.setBrush(QBrush(QColor(theme.bg_panel))); p.setPen(QPen(QColor(50,50,70),1))
            p.drawEllipse(QPointF(x,y),r,r)
            p.setPen(QPen(QColor(theme.text_light) if (in_scale or is_root) else QColor(theme.text_dim)))
            p.setFont(QFont('Segoe UI',9,QFont.Bold if is_root else QFont.Normal))
            p.drawText(QRectF(x-r,y-r,2*r,2*r), Qt.AlignCenter, MT.NOTES[nc])

        for i, nc in enumerate(MT.CIRCLE):
            rel=(nc+9)%12; angle=math.radians(i*30-90)
            x=cx+inner_r*math.cos(angle); y=cy+inner_r*math.sin(angle); in_s=rel in self.scale_notes
            r=12; c=QColor(theme.accent_green).darker(180) if in_s else QColor(theme.bg_dark)
            p.setBrush(QBrush(c)); p.setPen(QPen(QColor(50,50,70),1) if not in_s else QPen(QColor(theme.accent_green).darker(120),1))
            p.drawEllipse(QPointF(x,y),r,r)
            p.setPen(QPen(QColor(theme.text_light) if in_s else QColor(theme.text_dim))); p.setFont(QFont('Segoe UI',7))
            p.drawText(QRectF(x-r,y-r,2*r,2*r), Qt.AlignCenter, MT.NOTES[rel])

        p.setPen(QPen(QColor(theme.text_light))); p.setFont(QFont('Segoe UI',10,QFont.Bold))
        sig=MT.key_signature(self.root); sig_t=f' ({abs(sig)}{"♯" if sig>0 else "♭"})' if sig!=0 else ''
        p.drawText(QRectF(cx-55,cy-15,110,16), Qt.AlignCenter, MT.NOTES[self.root]+' Major'+sig_t)
        rel_m=(self.root+9)%12
        p.setFont(QFont('Segoe UI',8)); p.setPen(QPen(QColor(theme.accent_green)))
        p.drawText(QRectF(cx-55,cy+3,110,14), Qt.AlignCenter, 'Relative: '+MT.NOTES[rel_m]+' minor')
        p.end()

    def mousePressEvent(self, e):
        cx,cy=self.width()/2,self.height()/2; outer_r=min(self.width(),self.height())*0.42
        for i, nc in enumerate(MT.CIRCLE):
            angle=math.radians(i*30-90); x=cx+outer_r*math.cos(angle); y=cy+outer_r*math.sin(angle)
            if (e.position().x()-x)**2+(e.position().y()-y)**2<20**2: self.key_clicked.emit(nc); return


# ═══════════════════════════════════════════════════════════════
#  STAFF NOTATION
# ═══════════════════════════════════════════════════════════════
class StaffNotation(QWidget):
    DEG={0:0,2:1,4:2,5:3,7:4,9:5,11:6}; SHP={1:0,3:1,6:3,8:4,10:5}
    def __init__(self, parent=None):
        super().__init__(parent)
        self.notes=[]; self.title=''; self.key_root=0
        self.setMinimumHeight(160); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_notes(self, mn, title='', colors=None, key_root=0):
        self.notes=[(m, colors[i] if colors and i<len(colors) else QColor(theme.accent_blue)) for i,m in enumerate(mn)]
        self.title=title; self.key_root=key_root; self.update()

    def _pos(self, midi):
        oct=(midi//12)-1; note=midi%12; is_sharp=note not in self.DEG
        deg=self.SHP.get(note,0) if is_sharp else self.DEG[note]
        return -2+(oct-4)*7+deg, is_sharp

    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); p.fillRect(0,0,w,h,QColor(theme.bg_surface))
        ls=max(10,min(16,h/14)); st=h/2-2*ls; cy=st+4*ls
        if self.title: p.setPen(QPen(QColor(theme.text_light))); p.setFont(QFont('Segoe UI',9,QFont.Bold)); p.drawText(10,16,self.title)
        p.setPen(QPen(QColor(180,180,200))); p.setFont(QFont('Segoe UI',int(ls*4.2)))
        p.drawText(QRectF(6,st-ls,ls*3,ls*7), Qt.AlignCenter, '𝄞')
        nsx=ls*4.2; nex=w-10; p.setPen(QPen(QColor(80,80,100),1))
        for i in range(5): y=st+i*ls; p.drawLine(QPointF(nsx,y), QPointF(nex,y))
        if not self.notes: p.end(); return
        n=len(self.notes); avail=nex-nsx-30; sp=min(55,max(25,avail/max(n,1))); sx=nsx+15+max(0,(avail-n*sp)/2)
        for idx,(midi,color) in enumerate(self.notes):
            x=sx+idx*sp; pos,is_sharp=self._pos(midi); y=cy-pos*(ls/2)
            if pos<0:
                for lp in range(-2,pos-1,-1): ly=cy-lp*(ls/2); p.setPen(QPen(QColor(80,80,100),1)); p.drawLine(QPointF(x-9,ly),QPointF(x+9,ly))
            elif pos>8:
                for lp in range(10,pos+1): ly=cy-lp*(ls/2); p.setPen(QPen(QColor(80,80,100),1)); p.drawLine(QPointF(x-9,ly),QPointF(x+9,ly))
            if is_sharp: p.setPen(QPen(QColor(180,180,200))); p.setFont(QFont('Segoe UI',int(ls*1.0),QFont.Bold)); p.drawText(QRectF(x-16,y-ls*0.7,14,ls*1.4), Qt.AlignCenter, '♯')
            gr=QRadialGradient(x,y,ls*1.2); gc=QColor(color); gc.setAlpha(40)
            gr.setColorAt(0,gc); gr.setColorAt(1,QColor(0,0,0,0)); p.setBrush(QBrush(gr)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(x,y),ls*1.2,ls*0.8)
            p.setPen(QPen(color.darker(130),1.3)); p.setBrush(QBrush(color))
            p.save(); p.translate(x,y); p.rotate(-15); p.drawEllipse(QRectF(-5.5,-3.5,11,7)); p.restore()
            stem_up=pos<4; p.setPen(QPen(color,1.3))
            if stem_up: p.drawLine(QPointF(x+4.5,y-1),QPointF(x+4.5,y-ls*3))
            else: p.drawLine(QPointF(x-4.5,y+1),QPointF(x-4.5,y+ls*3))
            p.setPen(QPen(QColor(theme.text_dim))); p.setFont(QFont('Segoe UI',7))
            p.drawText(QRectF(x-15,cy+5.5*ls,30,12), Qt.AlignCenter, MT.NOTES[midi%12])
        p.end()


# ═══════════════════════════════════════════════════════════════
#  CHORD PROGRESSION WIDGET
# ═══════════════════════════════════════════════════════════════
class ProgressionWidget(QWidget):
    chord_selected = Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent); self.chords=[]; self.current=-1
        self.setMinimumHeight(70); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_chords(self, c, cur=-1): self.chords=c; self.current=cur; self.update()

    def paintEvent(self, e):
        p=QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        w,h=self.width(),self.height(); p.fillRect(0,0,w,h,QColor(theme.bg_surface))
        if not self.chords: p.setPen(QPen(QColor(theme.text_dim))); p.setFont(QFont('Segoe UI',10)); p.drawText(QRectF(0,0,w,h), Qt.AlignCenter, 'Select a progression'); p.end(); return
        n=len(self.chords); bw=min(110,(w-30)/max(n,1)); total=n*bw+(n-1)*6; sx=(w-total)/2
        for i,ch in enumerate(self.chords):
            x=sx+i*(bw+6); is_cur=(i==self.current); q=ch.get('quality','Major')
            col=QColor(theme.accent_gold) if is_cur else QColor(theme.bg_panel); border=QColor(theme.accent_gold) if is_cur else QColor(50,50,70)
            if is_cur:
                gr=QRadialGradient(x+bw/2,h/2,bw*0.8); gc=QColor(theme.accent_gold); gc.setAlpha(30)
                gr.setColorAt(0,gc); gr.setColorAt(1,QColor(0,0,0,0)); p.setBrush(QBrush(gr)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(x+bw/2,h/2),bw*0.8,h*0.5)
            p.setBrush(QBrush(col)); p.setPen(QPen(border,2 if is_cur else 1)); p.drawRoundedRect(QRectF(x,6,bw,h-12),6,6)
            tc=QColor(theme.bg_dark) if is_cur else QColor(theme.text_light); p.setPen(QPen(tc)); p.setFont(QFont('Segoe UI',11,QFont.Bold))
            p.drawText(QRectF(x,8,bw,(h-12)*0.55), Qt.AlignCenter, ch['roman'])
            p.setFont(QFont('Segoe UI',9)); p.drawText(QRectF(x,(h-12)*0.55+6,bw,(h-12)*0.45), Qt.AlignCenter, ch.get('symbol',''))
        p.end()

    def mousePressEvent(self, e):
        if not self.chords: return
        n=len(self.chords); bw=min(110,(self.width()-30)/max(n,1)); total=n*bw+(n-1)*6; sx=(self.width()-total)/2
        for i in range(n):
            x=sx+i*(bw+6)
            if x<=e.position().x()<=x+bw: self.current=i; self.chord_selected.emit(self.chords[i]['root']); self.update(); return


# ═══════════════════════════════════════════════════════════════
#  INFO PANEL
# ═══════════════════════════════════════════════════════════════
class InfoPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent); lay=QVBoxLayout(self); lay.setContentsMargins(6,6,6,6); lay.setSpacing(4)
        self.title_lbl=QLabel(''); self.title_lbl.setFont(QFont('Segoe UI',11,QFont.Bold)); self.title_lbl.setWordWrap(True); lay.addWidget(self.title_lbl)
        self.notes_lbl=QLabel(''); self.notes_lbl.setFont(QFont('Segoe UI',9)); self.notes_lbl.setWordWrap(True); lay.addWidget(self.notes_lbl)
        self.formula_lbl=QLabel(''); self.formula_lbl.setFont(QFont('Segoe UI',9)); self.formula_lbl.setWordWrap(True); lay.addWidget(self.formula_lbl)
        self.chords_lbl=QLabel(''); self.chords_lbl.setFont(QFont('Segoe UI',9)); self.chords_lbl.setWordWrap(True); lay.addWidget(self.chords_lbl)
        self.keys_lbl=QLabel(''); self.keys_lbl.setFont(QFont('Segoe UI',9)); self.keys_lbl.setWordWrap(True); lay.addWidget(self.keys_lbl)
        lay.addStretch()

    def update_info(self, root, scale_name, chord_type, mode):
        if mode == 'scale':
            notes=MT.get_scale_notes(root,scale_name); names=[MT.NOTES[n] for n in notes]
            self.title_lbl.setText(f'🎼 {MT.NOTES[root]} {scale_name}'); self.title_lbl.setStyleSheet(f'color:{theme.accent_blue};')
            self.notes_lbl.setText(f'Notes: <b>{" — ".join(names)}</b>'); self.notes_lbl.setStyleSheet(f'color:{theme.text_light};')
            formula=MT.scale_formula(scale_name); self.formula_lbl.setText(f'Formula: <b>{" — ".join(formula)}</b>'); self.formula_lbl.setStyleSheet(f'color:{theme.accent_gold};')
            diatonic=MT.get_diatonic_chords(root,scale_name)
            self.chords_lbl.setText('Diatonic: '+'  '.join(f'<b>{d["roman"]}</b>({MT.NOTES[d["root"]]})' for d in diatonic)); self.chords_lbl.setStyleSheet(f'color:{theme.accent_green};')
            sig=MT.key_signature(root); sig_str=f'{abs(sig)}{"♯" if sig>0 else "♭"}' if sig!=0 else '0'
            rel=(root+9)%12; self.keys_lbl.setText(f'Relative minor: <b>{MT.NOTES[rel]}</b> | Key sig: <b>{sig_str}</b>'); self.keys_lbl.setStyleSheet(f'color:{theme.accent_purple};')
        elif mode == 'chord':
            notes=MT.get_chord_notes(root,chord_type); names=[MT.NOTES[n] for n in notes]; sym=MT.chord_symbol(root,chord_type)
            self.title_lbl.setText(f'🎵 {sym}'); self.title_lbl.setStyleSheet(f'color:{theme.accent_red};')
            self.notes_lbl.setText(f'Notes: <b>{" — ".join(names)}</b>'); self.notes_lbl.setStyleSheet(f'color:{theme.text_light};')
            self.formula_lbl.setText(''); self.chords_lbl.setText(''); self.keys_lbl.setText('')
        elif mode == 'progression':
            self.title_lbl.setText('🎸 Progression'); self.title_lbl.setStyleSheet(f'color:{theme.accent_green};')
            self.notes_lbl.setText(''); self.formula_lbl.setText(''); self.chords_lbl.setText(''); self.keys_lbl.setText('')


# ═══════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('♪ Music Theory Visualizer — YouTube Edition v3.0')
        self.setMinimumSize(1100,700); self.resize(1440,850)
        self.root=0; self.scale_name='Major'; self.chord_type='Major'
        self.mode='scale'; self.prog_name=list(MT.PROGRESSIONS.keys())[0]; self.bpm=120
        self.is_playing=False

        self.audio=AudioEngine(); self.recorder=VideoRecorder(self, self.audio)
        self.anim_timer=QTimer(); self.anim_timer.timeout.connect(self._anim_step)
        self.anim_notes=[]; self.anim_idx=0; self.prog_chords=[]

        self._build_ui(); self._apply_dark_theme(); self._refresh_all(); self._setup_shortcuts()

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key_Space),self,self._on_play)
        QShortcut(QKeySequence(Qt.Key_Escape),self,self._on_stop)
        QShortcut(Qt.Key_Left,self,lambda:self._transpose(-1))
        QShortcut(Qt.Key_Right,self,lambda:self._transpose(1))

    def _build_ui(self):
        central=QWidget(); self.setCentralWidget(central)
        main_h=QHBoxLayout(central); main_h.setSpacing(4); main_h.setContentsMargins(4,4,4,4)

        # LEFT PANEL
        left=QWidget(); left.setFixedWidth(240); left.setStyleSheet(f'background:{theme.bg_panel}; border-radius:8px;')
        lv=QVBoxLayout(left); lv.setContentsMargins(8,8,8,8); lv.setSpacing(3)

        self.mode_tabs=QTabWidget()
        for m in ['Scale','Chord','Prog']: self.mode_tabs.addTab(QWidget(),m)
        self.mode_tabs.currentChanged.connect(self._on_mode_changed); lv.addWidget(self.mode_tabs)

        lv.addWidget(QLabel('Root Note:'))
        self.root_combo=QComboBox(); self.root_combo.addItems(MT.NOTES); self.root_combo.currentIndexChanged.connect(self._on_root_changed); lv.addWidget(self.root_combo)
        tr_h=QHBoxLayout()
        btn_tdown=QPushButton('♭'); btn_tdown.setFixedWidth(35); btn_tdown.clicked.connect(lambda:self._transpose(-1))
        btn_tup=QPushButton('♯'); btn_tup.setFixedWidth(35); btn_tup.clicked.connect(lambda:self._transpose(1))
        tr_h.addWidget(btn_tdown); tr_h.addWidget(btn_tup); lv.addLayout(tr_h)

        self.scale_combo=QComboBox(); self.scale_combo.addItems(MT.SCALES.keys()); self.scale_combo.currentTextChanged.connect(self._on_scale_changed)
        self.scale_label=QLabel('Scale:'); lv.addWidget(self.scale_label); lv.addWidget(self.scale_combo)

        self.chord_combo=QComboBox(); self.chord_combo.addItems(MT.CHORD_TYPES.keys()); self.chord_combo.currentTextChanged.connect(self._on_chord_changed)
        self.chord_label=QLabel('Chord Type:'); lv.addWidget(self.chord_label); lv.addWidget(self.chord_combo)

        self.prog_combo=QComboBox(); self.prog_combo.addItems(MT.PROGRESSIONS.keys()); self.prog_combo.currentTextChanged.connect(self._on_prog_changed)
        self.prog_label=QLabel('Progression:'); lv.addWidget(self.prog_label); lv.addWidget(self.prog_combo)

        bpm_h=QHBoxLayout(); bpm_h.addWidget(QLabel('BPM:')); self.bpm_spin=QSpinBox(); self.bpm_spin.setRange(30,300); self.bpm_spin.setValue(120); self.bpm_spin.valueChanged.connect(lambda v:setattr(self,'bpm',v)); bpm_h.addWidget(self.bpm_spin); lv.addLayout(bpm_h)
        wt_h=QHBoxLayout(); wt_h.addWidget(QLabel('Sound:')); self.wave_combo=QComboBox(); self.wave_combo.addItems(['Piano','Sine','Synth']); self.wave_combo.currentTextChanged.connect(lambda t:setattr(self.audio,'wave_type',t)); wt_h.addWidget(self.wave_combo); lv.addLayout(wt_h)

        self.show_names_chk=QCheckBox('Note Names'); self.show_names_chk.setChecked(True); self.show_names_chk.toggled.connect(lambda v:setattr(self.piano,'show_names',v)); lv.addWidget(self.show_names_chk)
        self.show_degrees_chk=QCheckBox('Scale Degrees'); self.show_degrees_chk.toggled.connect(self._on_show_degrees); lv.addWidget(self.show_degrees_chk)
        self.glow_chk=QCheckBox('Glow Effects'); self.glow_chk.setChecked(True); self.glow_chk.toggled.connect(lambda v:setattr(self.piano,'glow_enabled',v)); lv.addWidget(self.glow_chk)
        self.guitar_chk=QCheckBox('Guitar Fretboard'); self.guitar_chk.setChecked(True); self.guitar_chk.toggled.connect(lambda v:self.guitar.setVisible(v)); lv.addWidget(self.guitar_chk)

        th_h=QHBoxLayout(); th_h.addWidget(QLabel('Theme:')); self.theme_combo=QComboBox(); self.theme_combo.addItems(theme.names); self.theme_combo.currentTextChanged.connect(self._on_theme_changed); th_h.addWidget(self.theme_combo); lv.addLayout(th_h)
        lo_h=QHBoxLayout(); lo_h.addWidget(QLabel('Layout:')); self.layout_combo=QComboBox(); self.layout_combo.addItems(['Landscape 16:9','Portrait 9:16','Square 1:1','Free']); self.layout_combo.currentTextChanged.connect(self._on_layout_changed); lo_h.addWidget(self.layout_combo); lv.addLayout(lo_h)

        # Playback & Record
        lv.addWidget(QLabel('Playback & Record:'))
        pb_h=QHBoxLayout()
        self.play_btn=QPushButton('▶ Play'); self.play_btn.clicked.connect(self._on_play); pb_h.addWidget(self.play_btn)
        self.arp_btn=QPushButton('♪ Arp'); self.arp_btn.clicked.connect(self._on_arpeggio); pb_h.addWidget(self.arp_btn)
        self.stop_btn=QPushButton('■ Stop'); self.stop_btn.setFixedWidth(50); self.stop_btn.clicked.connect(self._on_stop); pb_h.addWidget(self.stop_btn)
        lv.addLayout(pb_h)

        self.rec_btn=QPushButton('⏺ Record to MP4'); self.rec_btn.setStyleSheet(f'color:{theme.accent_red}; font-weight:bold; font-size:13px; padding:8px;')
        self.rec_btn.clicked.connect(self._on_record_toggle); lv.addWidget(self.rec_btn)
        self.rec_status=QLabel(''); self.rec_status.setAlignment(Qt.AlignCenter); self.rec_status.setStyleSheet(f'color:{theme.accent_red};'); lv.addWidget(self.rec_status)

        lv.addWidget(QLabel('Title Overlay:'))
        self.title_edit=QLineEdit(); self.title_edit.setPlaceholderText('e.g. C Major Scale'); self.title_edit.textChanged.connect(lambda t:self.overlay_title.setText(t)); lv.addWidget(self.title_edit)
        lv.addStretch(); main_h.addWidget(left)

        # RIGHT AREA
        self.main_splitter=QSplitter(Qt.Vertical)

        # Title + Piano
        piano_box=QWidget(); pv=QVBoxLayout(piano_box); pv.setContentsMargins(0,0,0,0)
        self.overlay_title=QLabel(''); self.overlay_title.setAlignment(Qt.AlignCenter); self.overlay_title.setFont(QFont('Segoe UI',16,QFont.Bold)); self.overlay_title.setStyleSheet(f'color:{theme.accent_gold}; background:transparent;'); self.overlay_title.setMaximumHeight(30); pv.addWidget(self.overlay_title)
        self.piano=PianoKeyboard(); self.piano.note_clicked.connect(lambda m:self.audio.play_note(m,0.4)); pv.addWidget(self.piano)
        self.main_splitter.addWidget(piano_box)

        # Middle row
        mid=QWidget(); mid_h=QHBoxLayout(mid); mid_h.setContentsMargins(0,0,0,0); mid_h.setSpacing(4)
        self.circle=CircleOfFifths(); self.circle.key_clicked.connect(self._on_circle_key); mid_h.addWidget(self.circle,4)
        vis_tabs=QTabWidget(); self.staff=StaffNotation(); vis_tabs.addTab(self.staff,'Staff'); mid_h.addWidget(vis_tabs,5)
        self.info=InfoPanel(); mid_h.addWidget(self.info,3)
        self.main_splitter.addWidget(mid)

        # Guitar
        self.guitar=GuitarFretboard(); self.main_splitter.addWidget(self.guitar)

        # Progression
        self.prog_widget=ProgressionWidget(); self.prog_widget.chord_selected.connect(self._on_prog_chord); self.main_splitter.addWidget(self.prog_widget)

        self.main_splitter.setSizes([190,310,100,70]); main_h.addWidget(self.main_splitter,1)

        self.statusBar().showMessage('Ready — Hit ⏺ Record to capture Play+Audio to MP4')

        self._update_mode_visibility()

    def _apply_dark_theme(self):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background:{theme.bg_dark}; color:{theme.text_light}; font-family:'Segoe UI',Arial,sans-serif; }}
            QComboBox, QSpinBox, QLineEdit {{ background:{theme.bg_surface}; color:{theme.text_light}; border:1px solid #333355; border-radius:4px; padding:3px 6px; min-height:22px; }}
            QComboBox::drop-down {{ border:none; }} QComboBox QAbstractItemView {{ background:{theme.bg_surface}; color:{theme.text_light}; selection-background-color:#333366; }}
            QPushButton {{ background:{theme.bg_surface}; color:{theme.text_light}; border:1px solid #333355; border-radius:5px; padding:4px 8px; font-weight:bold; }}
            QPushButton:hover {{ background:#2a2a44; border-color:{theme.accent_blue}; }} QPushButton:pressed {{ background:#1a1a33; }}
            QLabel {{ color:{theme.text_light}; }}
            QTabWidget::pane {{ border:1px solid #333355; background:{theme.bg_panel}; }}
            QTabBar::tab {{ background:{theme.bg_dark}; color:{theme.text_dim}; padding:5px 10px; border:1px solid #333355; border-bottom:none; border-top-left-radius:5px; border-top-right-radius:5px; }}
            QTabBar::tab:selected {{ background:{theme.bg_panel}; color:{theme.accent_blue}; }}
            QCheckBox {{ color:{theme.text_light}; spacing:5px; }}
            QSplitter::handle {{ background:#333355; height:3px; }}
            QStatusBar {{ background:{theme.bg_panel}; color:{theme.text_dim}; font-size:11px; }}
        """)

    def _on_theme_changed(self, n): theme.apply(n); self._apply_dark_theme(); self._refresh_all()
    def _on_layout_changed(self, l):
        if l=='Landscape 16:9': self.resize(1280,720)
        elif l=='Portrait 9:16': self.resize(405,720)
        elif l=='Square 1:1': self.resize(720,720)

    def _update_mode_visibility(self):
        m=self.mode
        self.scale_combo.setVisible(m=='scale'); self.scale_label.setVisible(m=='scale')
        self.chord_combo.setVisible(m=='chord'); self.chord_label.setVisible(m=='chord')
        self.prog_combo.setVisible(m=='progression'); self.prog_label.setVisible(m=='progression')
        self.prog_widget.setVisible(m=='progression')

    def _on_mode_changed(self, idx):
        modes=['scale','chord','progression']
        if 0<=idx<3: self.mode=modes[idx]
        self._update_mode_visibility(); self._refresh_all()

    def _on_root_changed(self, i): self.root=i; self._refresh_all()
    def _on_scale_changed(self, t): self.scale_name=t; self._refresh_all()
    def _on_chord_changed(self, t): self.chord_type=t; self._refresh_all()
    def _on_prog_changed(self, t): self.prog_name=t; self._refresh_all()
    def _on_circle_key(self, n): self.root=n; self.root_combo.setCurrentIndex(n); self._refresh_all()
    def _on_show_degrees(self, v): self.piano.show_degrees=v; self.guitar.show_degrees=v; self._refresh_all()
    def _transpose(self, s): self.root=(self.root+s)%12; self.root_combo.setCurrentIndex(self.root); self._refresh_all()
    def _on_prog_chord(self, r):
        notes=MT.get_chord_notes(r,'Major'); self.piano.set_highlighted(notes,root=r); self.guitar.set_highlighted(notes,root=r)
        self.audio.play_chord([60+r,60+r+4,60+r+7],0.8)

    def _refresh_all(self):
        r=self.root
        if self.mode=='scale':
            notes=MT.get_scale_notes(r,self.scale_name); self.piano.set_highlighted(notes,root=r); self.piano.set_degree_map(r,self.scale_name)
            self.guitar.set_highlighted(notes,root=r); self.guitar.set_degree_map(r,self.scale_name)
            diatonic=MT.get_diatonic_chords(r,self.scale_name); self.circle.set_data(r,notes,diatonic)
            mn=[60+r+i for i in MT.SCALES[self.scale_name]]; mn.append(60+r+12)
            c=[QColor(theme.accent_red) if i==0 else QColor(theme.accent_blue) for i in range(len(MT.SCALES[self.scale_name]))]; c.append(QColor(theme.accent_red))
            self.staff.set_notes(mn,title=f'{MT.NOTES[r]} {self.scale_name}',colors=c,key_root=r)
            self.info.update_info(r,self.scale_name,self.chord_type,'scale')
            self.title_edit.setText(f'{MT.NOTES[r]} {self.scale_name} Scale')
        elif self.mode=='chord':
            notes=MT.get_chord_notes(r,self.chord_type); self.piano.set_highlighted(notes,root=r); self.piano.set_degree_map(r,'Major')
            self.guitar.set_highlighted(notes,root=r); self.guitar.set_degree_map(r,'Major')
            self.circle.set_data(r,notes,[])
            mn=[60+r+i for i in MT.CHORD_TYPES[self.chord_type]]
            c=[QColor(theme.accent_red) if i==0 else QColor(theme.accent_blue) for i in range(len(MT.CHORD_TYPES[self.chord_type]))]
            self.staff.set_notes(mn,title=MT.chord_symbol(r,self.chord_type),colors=c,key_root=r)
            self.info.update_info(r,self.scale_name,self.chord_type,'chord')
            self.title_edit.setText(MT.chord_symbol(r,self.chord_type))
        elif self.mode=='progression':
            pi=MT.PROGRESSIONS[self.prog_name]; si=MT.SCALES['Major']; da=MT.get_diatonic_chords(r,'Major')
            chords=[]; all_notes=set()
            for p in pi:
                for j,s in enumerate(si):
                    if s==p%12 and j<len(da): chords.append(da[j]); all_notes.update(da[j]['notes']); break
            self.piano.set_highlighted(list(all_notes),root=r); self.piano.set_degree_map(r,'Major')
            self.guitar.set_highlighted(list(all_notes),root=r); self.guitar.set_degree_map(r,'Major')
            self.circle.set_data(r,list(all_notes),da); self.prog_widget.set_chords(chords)
            ml=[]; cl=[]
            for ch in chords:
                for offset in MT.CHORD_TYPES.get(ch['quality'],[0,4,7]): ml.append(60+ch['root']+offset); cl.append(QColor(theme.accent_red) if ch['root']==r else QColor(theme.accent_blue))
            self.staff.set_notes(ml[:16],title=self.prog_name,colors=cl[:16],key_root=r)
            self.info.update_info(r,self.scale_name,self.chord_type,'progression')
            self.title_edit.setText(f'{MT.NOTES[r]} — {self.prog_name}')

    # ── Playback ─────────────────────────────────────────────
    def _on_play(self):
        if self.is_playing: self._on_stop(); return
        self.is_playing=True; self.play_btn.setText('⏸')
        if self.mode=='scale':
            iv=MT.SCALES[self.scale_name]; self.anim_notes=[60+self.root+i for i in iv]; self.anim_notes.append(60+self.root+12)
            self.audio.play_scale(self.anim_notes,note_dur=max(0.1,60/self.bpm/2),gap=0.04,vol=0.35)
            self.anim_idx=0; ms=max(80,int(60000/self.bpm/2)); self.anim_timer.start(ms); self._anim_step()
        elif self.mode=='chord':
            iv=MT.CHORD_TYPES[self.chord_type]; midis=[60+self.root+i for i in iv]
            self.audio.play_chord(midis,1.5); self.anim_notes=[]; self.piano.anim_note=None; self.piano.update()
            QTimer.singleShot(1500,self._on_stop)
        elif self.mode=='progression': self._play_prog()

    def _on_arpeggio(self):
        if self.is_playing: self._on_stop(); return
        self.is_playing=True; self.arp_btn.setText('⏸')
        if self.mode=='chord': self.anim_notes=[60+self.root+i for i in MT.CHORD_TYPES[self.chord_type]]
        elif self.mode=='scale': self.anim_notes=[60+self.root+i for i in MT.SCALES[self.scale_name]]; self.anim_notes.append(60+self.root+12)
        elif self.mode=='progression': self._play_prog_arp(); return
        else: return
        self.anim_idx=0; ms=max(60,int(60000/self.bpm/2)); self.anim_timer.start(ms); self._anim_step()

    def _play_prog(self):
        pi=MT.PROGRESSIONS[self.prog_name]; si=MT.SCALES['Major']; da=MT.get_diatonic_chords(self.root,'Major')
        self.anim_notes=[]; self.prog_chords=[]
        for p in pi:
            for j,s in enumerate(si):
                if s==p%12 and j<len(da):
                    ch=da[j]; midis=[60+ch['root']+o for o in MT.CHORD_TYPES.get(ch['quality'],[0,4,7])]
                    self.anim_notes.append(midis); self.prog_chords.append(ch); break
        self.anim_idx=0; ms=max(200,int(60000/self.bpm)); self.anim_timer.start(ms); self._anim_step()

    def _play_prog_arp(self):
        pi=MT.PROGRESSIONS[self.prog_name]; si=MT.SCALES['Major']; da=MT.get_diatonic_chords(self.root,'Major')
        self.anim_notes=[]; self.prog_chords=[]; all_s=[]
        for p in pi:
            for j,s in enumerate(si):
                if s==p%12 and j<len(da):
                    ch=da[j]; midis=[60+ch['root']+o for o in MT.CHORD_TYPES.get(ch['quality'],[0,4,7])]
                    all_s.extend(midis); self.prog_chords.append(ch); break
        self.anim_notes=all_s; self.anim_idx=0; ms=max(60,int(60000/self.bpm/2)); self.anim_timer.start(ms); self._anim_step()

    def _anim_step(self):
        if self.anim_idx>=len(self.anim_notes): self._on_stop(); return
        item=self.anim_notes[self.anim_idx]
        if isinstance(item,list):
            self.audio.play_chord(item,0.8); nc=[m%12 for m in item]; self.piano.set_highlighted(nc,root=item[0]%12); self.piano.anim_note=None; self.piano.update()
            if self.anim_idx<len(self.prog_chords):
                self.prog_widget.current=self.anim_idx; self.prog_widget.update(); ch=self.prog_chords[self.anim_idx]
                self.guitar.set_highlighted(ch['notes'],root=ch['root'])
        else:
            self.audio.play_note(item,max(0.1,60/self.bpm/2),0.35); self.piano.anim_note=item; self.piano.update(); self.guitar.update()
        self.anim_idx+=1

    def _on_stop(self):
        self.anim_timer.stop(); self.is_playing=False; self.play_btn.setText('▶ Play'); self.arp_btn.setText('♪ Arp')
        self.piano.anim_note=None; self.piano.update(); self.prog_widget.current=-1; self.prog_widget.update()
        self.audio.stop()
        if self.recorder.is_recording: self._stop_recording()
        self.statusBar().showMessage('Ready'); self._refresh_all()

    # ── Recording ────────────────────────────────────────────
    def _on_record_toggle(self):
        if self.recorder.is_recording: self._on_stop() # Stop triggers _stop_recording
        else: self._start_recording()

    def _start_recording(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 Files (*.mp4)")
        if not path: return
        if not path.endswith('.mp4'): path += '.mp4'
        
        self.recorder.fps = 30
        self.recorder.start(path)
        self.rec_btn.setText('■ Stop Rec')
        self.rec_status.setText(f'Recording 30fps...')
        self.statusBar().showMessage('● REC — Playing animation...')
        
        # Auto-trigger play
        if not self.is_playing: self._on_play()

    def _stop_recording(self):
        self.rec_status.setText('Encoding...')
        self.rec_btn.setText('⏺ Record to MP4')
        # Need to delay encoding slightly to let the UI update
        QTimer.singleShot(100, self._do_encode)

    def _do_encode(self):
        self.setDisabled(True)
        self.recorder.stop_and_encode()
        self.setDisabled(False)
        self.rec_status.setText('')


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════
def main():
    app=QApplication(sys.argv); app.setStyle('Fusion')
    pal=app.palette()
    pal.setColor(pal.ColorRole.Window,QColor(theme.bg_dark)); pal.setColor(pal.ColorRole.WindowText,QColor(theme.text_light))
    pal.setColor(pal.ColorRole.Base,QColor(theme.bg_surface)); pal.setColor(pal.ColorRole.AlternateBase,QColor(theme.bg_panel))
    pal.setColor(pal.ColorRole.Text,QColor(theme.text_light)); pal.setColor(pal.ColorRole.Button,QColor(theme.bg_surface))
    pal.setColor(pal.ColorRole.ButtonText,QColor(theme.text_light)); pal.setColor(pal.ColorRole.Highlight,QColor(theme.accent_blue))
    pal.setColor(pal.ColorRole.HighlightedText,QColor(theme.bg_dark))
    app.setPalette(pal)
    win=MainWindow(); win.show()
    sys.exit(app.exec())

if __name__=='__main__': main()