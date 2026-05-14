import sys, numpy as np, sounddevice as sd
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox
from PyQt6.QtCore import QTimer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.patches import Polygon
from matplotlib.animation import FuncAnimation

# ---------------- CONFIG ----------------
fs = 44100
base_quarter_duration = 0.6
note_durations = {"eighth":0.3,"quarter":0.6,"half":1.2,"whole":2.4}

notes_list = ["C","G","D","A","E","B","F#","C#","Ab","Eb","Bb","F"]
N = len(notes_list)
angles = np.linspace(0,2*np.pi,N,endpoint=False)
radius=1.0
note_positions={notes_list[i]:(radius*np.cos(angles[i]),radius*np.sin(angles[i])) for i in range(N)}
note_freqs={"C":261.63,"C#":277.18,"D":293.66,"Eb":311.13,"E":329.63,"F":349.23,"F#":369.99,
            "G":392.00,"Ab":415.30,"A":440.00,"Bb":466.16,"B":493.88}

# ---------------- MODES & ROMAN ----------------
modes={"Ionian":[0,2,4,5,7,9,11],"Dorian":[0,2,3,5,7,9,10],"Phrygian":[0,1,3,5,7,8,10],
       "Lydian":[0,2,4,6,7,9,11],"Mixolydian":[0,2,4,5,7,9,10],"Aeolian":[0,2,3,5,7,8,10],
       "Locrian":[0,1,3,5,6,8,10]}
mode_roman={"Ionian":["I","ii","iii","IV","V","vi","vii°"],
            "Dorian":["i","ii","bIII","IV","v","vi°","bVII"],
            "Phrygian":["i","bII","bIII","iv","v°","bVI","bVII"],
            "Lydian":["I","II","iii","#iv°","V","vi","vii"],
            "Mixolydian":["I","ii","iii°","IV","v","vi","bVII"],
            "Aeolian":["i","ii°","bIII","iv","v","bVI","bVII"],
            "Locrian":["i°","bII","bIII","iv","bV","bVI","bVII"]}

note_to_pc={"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"F":5,"F#":6,"Gb":6,"G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11}

def chord_to_roman(chord, tonic, mode="Ionian"):
    if not chord: return "?"
    root = chord[0]
    root_pc = note_to_pc.get(root, -1)
    tonic_pc = note_to_pc.get(tonic,0)
    scale_pc = [(tonic_pc + step)%12 for step in modes[mode]]
    if root_pc in scale_pc:
        idx = scale_pc.index(root_pc)
        return mode_roman[mode][idx]
    # secondary dominants
    for i, deg in enumerate(scale_pc):
        if root_pc == (deg+7)%12:
            return f"V/{mode_roman[mode][i]}"
    return f"(non-diatonic {root})"

# ---------------- SYNTH ----------------
def generate_note_synth(freq,duration=0.5,fs=44100):
    t = np.linspace(0,duration,int(fs*duration),endpoint=False)
    harmonics=[1,0.5,0.25,0.15,0.1]
    signal=np.zeros_like(t)
    for i,amp in enumerate(harmonics):
        signal+=amp*np.sin(2*np.pi*freq*(i+1)*t)
    # simple ADSR
    A=int(0.05*fs); D=int(0.1*fs); R=int(0.15*fs); S=0.7
    env=np.ones_like(t)*S
    if A>0: env[:A]=np.linspace(0,1,A)
    if D>0: env[A:A+D]=np.linspace(1,S,D)
    if R>0: env[-R:]=np.linspace(S,0,R)
    signal*=env
    signal/=np.max(np.abs(signal))
    return signal

# ---------------- NOTE DOT ----------------
class NoteDot:
    def __init__(self,note,ax,color="red"):
        self.note = note
        self.x,self.y = note_positions[note]
        self.dot, = ax.plot([self.x],[self.y],'o',color=color,markersize=8)
        self.trail, = ax.plot([],[], '-', color=color, alpha=0.4, linewidth=1.5)
        self.trail_x,self.trail_y=[],[]
    def move_toward(self,target,alpha):
        tx,ty = note_positions[target]
        x = self.x + (tx - self.x)*alpha
        y = self.y + (ty - self.y)*alpha
        self.dot.set_data([x],[y])
        self.trail_x.append(x)
        self.trail_y.append(y)
        if len(self.trail_x)>50:  # max trail length
            self.trail_x=self.trail_x[-50:]
            self.trail_y=self.trail_y[-50:]
        self.trail.set_data(self.trail_x,self.trail_y)
        return x,y
    def update_position(self,target):
        self.x,self.y = note_positions[target]

# ---------------- MAIN APP ----------------
class CircleOfFifthsApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Circle of Fifths Visualizer")
        self.setGeometry(100,100,950,950)
        layout=QVBoxLayout()
        self.label=QLabel("Enter sequence (notes or chords) with duration (quarter/half/whole/eighth), e.g., C:quarter, E G B:half")
        layout.addWidget(self.label)
        self.input_line=QLineEdit()
        layout.addWidget(self.input_line)
        self.key_box = QComboBox(); self.key_box.addItems(["C","G","D","A","E","B","F","Bb","Eb","Ab","Db","Gb"])
        layout.addWidget(QLabel("Select Key")); layout.addWidget(self.key_box)
        self.mode_box = QComboBox(); self.mode_box.addItems(list(modes.keys()))
        layout.addWidget(QLabel("Select Mode")); layout.addWidget(self.mode_box)
        self.btn = QPushButton("Analyze & Animate"); layout.addWidget(self.btn)
        self.info_label=QLabel("Chord info will appear here"); layout.addWidget(self.info_label)
        self.canvas=FigureCanvas(plt.Figure(figsize=(7,7))); layout.addWidget(self.canvas)
        self.setLayout(layout)
        self.ax=self.canvas.figure.add_subplot(111)
        self.ax.set_xlim(-1.3,1.3); self.ax.set_ylim(-1.3,1.3); self.ax.set_aspect('equal'); self.ax.axis('off')
        self.btn.clicked.connect(self.generate_progression)
        self.ani=None
        self.dots=[]
        self.sequence=[]
        self.t=0
        self.idx=0
        self.base_frames=30
        self.chord_shapes=[]
    def parse_input(self,text):
        events=[]
        for item in text.split(","):
            parts = item.strip().split(":")
            chord_notes=parts[0].split()
            duration = parts[1] if len(parts)>1 else "quarter"
            events.append({"chord":chord_notes,"duration":duration})
        return events
    def generate_progression(self):
        self.ax.clear(); self.ax.set_xlim(-1.3,1.3); self.ax.set_ylim(-1.3,1.3); self.ax.set_aspect('equal'); self.ax.axis('off')
        tonic = self.key_box.currentText()
        mode = self.mode_box.currentText()
        # draw notes
        for note,(x,y) in note_positions.items():
            self.ax.text(x,y,note,ha='center',va='center',fontsize=12,fontweight='bold')
        self.sequence = self.parse_input(self.input_line.text())
        if not self.sequence: return
        self.dots=[]; self.chord_shapes=[]
        first_event = self.sequence[0]
        for note in first_event["chord"]:
            self.dots.append(NoteDot(note,self.ax))
        self.idx=0; self.t=0
        if self.ani: self.ani.event_source.stop()
        self.ani=FuncAnimation(self.canvas.figure,self.animate,frames=2000,interval=50,blit=True)
        self.canvas.draw()
    def animate(self,frame):
        event = self.sequence[self.idx]
        chord = event["chord"]
        duration = event["duration"]
        frames_for_this = int(self.base_frames * note_durations[duration]/base_quarter_duration)
        alpha = self.t/frames_for_this
        start_chord = self.sequence[self.idx-1]["chord"] if self.idx>0 else chord
        # move dots
        for i,note in enumerate(chord):
            self.dots[i%len(self.dots)].move_toward(note,alpha)
        # on arrival
        if self.t==frames_for_this:
            tonic=self.key_box.currentText(); mode=self.mode_box.currentText()
            roman=chord_to_roman(chord,tonic,mode)
            self.info_label.setText(f"Chord {chord} → {roman} in {tonic} {mode}")
            # chord polygon
            poly = Polygon([note_positions[n] for n in chord if n in note_positions],closed=True,fill=False,edgecolor="cyan",linewidth=1.5,alpha=0.5)
            self.ax.add_patch(poly); self.chord_shapes.append(poly)
            # play chord
            mix=np.zeros(int(fs*note_durations[duration]))
            for n in chord:
                if n in note_freqs:
                    sig=generate_note_synth(note_freqs[n],duration=note_durations[duration],fs=fs)
                    mix[:len(sig)] += sig
            mix/=np.max(np.abs(mix)) if np.max(np.abs(mix))>0 else 1
            stereo = np.stack([mix,mix],axis=1)
            sd.play(stereo,fs,blocking=False)
            # update positions
            for i,note in enumerate(chord): self.dots[i%len(self.dots)].update_position(note)
            self.idx=(self.idx+1)%len(self.sequence); self.t=0
        else: self.t+=1
        return [d.dot for d in self.dots] + [d.trail for d in self.dots] + self.chord_shapes

# ---------------- RUN ----------------
if __name__=="__main__":
    app=QApplication(sys.argv)
    w=CircleOfFifthsApp()
    w.show()
    sys.exit(app.exec())
