from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QSpinBox, QTabWidget, QSplitter, QCheckBox, 
    QFileDialog, QSizePolicy, QLineEdit)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence, QFont, QColor

from theme import theme
from theory import MT
from audio_engine import AudioEngine
from video_recorder import VideoRecorder
from widgets_piano import PianoKeyboard
from widgets_fretboard import GuitarFretboard
from widgets_circle import CircleOfFifths
from widgets_misc import StaffNotation, ProgressionWidget, InfoPanel

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
        # Delay encoding slightly to let UI update
        QTimer.singleShot(100, self._do_encode)

    def _do_encode(self):
        self.setDisabled(True)
        self.recorder.stop_and_encode()
        self.setDisabled(False)
        self.rec_status.setText('')