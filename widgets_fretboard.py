from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QRadialGradient
from theme import theme
from theory import MT

class GuitarFretboard(QWidget):
    TUNING=[40,45,50,55,59,64]; SNAMES=['E','A','D','G','B','e']
    MARKERS=[3,5,7,9,12,15,17,19,21]; DMARKS=[12]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighted=set(); self.root_class=None; self.num_frets=21
        self.show_degrees=False; self._degree_map={}
        self.setMinimumHeight(110); self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_highlighted(self, nc, root=None): self.highlighted=set(nc); self.root_class=root; self.update()
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
            if f in self.DMARKS: p.drawEllipse(QPointF(cx,cy-fh*0.18),4,4); p.drawEllipse(QPointF(cx,cy+fh*0.18),4,4)
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