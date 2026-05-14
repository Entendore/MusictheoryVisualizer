from PySide6.QtWidgets import QWidget, QSizePolicy, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QRadialGradient
from theme import theme
from theory import MT

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