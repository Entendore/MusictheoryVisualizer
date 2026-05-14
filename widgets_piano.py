from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QLinearGradient, QRadialGradient
from theme import theme
from theory import MT

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