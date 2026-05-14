import math
from PySide6.QtWidgets import QWidget, QSizePolicy
from PySide6.QtCore import Qt, QRectF, QPointF, Signal
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QRadialGradient
from theme import theme
from theory import MT

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