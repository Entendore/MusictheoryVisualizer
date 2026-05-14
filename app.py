#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor 
from PySide6.QtCore import Qt
from main_window import MainWindow
from theme import theme

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    pal = app.palette()
    pal.setColor(pal.ColorRole.Window, QColor(theme.bg_dark))
    pal.setColor(pal.ColorRole.WindowText, QColor(theme.text_light))
    pal.setColor(pal.ColorRole.Base, QColor(theme.bg_surface))
    pal.setColor(pal.ColorRole.AlternateBase, QColor(theme.bg_panel))
    pal.setColor(pal.ColorRole.Text, QColor(theme.text_light))
    pal.setColor(pal.ColorRole.Button, QColor(theme.bg_surface))
    pal.setColor(pal.ColorRole.ButtonText, QColor(theme.text_light))
    pal.setColor(pal.ColorRole.Highlight, QColor(theme.accent_blue))
    pal.setColor(pal.ColorRole.HighlightedText, QColor(theme.bg_dark))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()