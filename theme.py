from PySide6.QtGui import QColor

class ThemeManager:
    THEMES = {
        'Neon': dict(bg_dark='#0f0f1a', bg_surface='#161625', bg_panel='#1c1c30', accent_blue='#53d8fb', accent_red='#e94560', accent_gold='#ffd93d', accent_green='#6bcb77', accent_purple='#b06cff', accent_orange='#ff8c42', text_light='#eaeaea', text_dim='#888899', piano_white='#f0f0f0', piano_black='#1a1a1a', wood='#6B4F2A', fret='#d0d0d0', string='#c0c0c0'),
        'Midnight': dict(bg_dark='#050510', bg_surface='#0a0a18', bg_panel='#101025', accent_blue='#4488ff', accent_red='#ff4466', accent_gold='#ffcc33', accent_green='#44dd88', accent_purple='#8855ff', accent_orange='#ff7744', text_light='#d0d8f0', text_dim='#556688', piano_white='#e8e8f0', piano_black='#0a0a15', wood='#3E2F1C', fret='#808080', string='#909090'),
        'Sunset': dict(bg_dark='#1a0f0f', bg_surface='#251616', bg_panel='#301c1c', accent_blue='#66bbee', accent_red='#ff6655', accent_gold='#ffaa33', accent_green='#55cc77', accent_purple='#cc66ff', accent_orange='#ff8833', text_light='#f0e8e8', text_dim='#997777', piano_white='#f8f0f0', piano_black='#1a1010', wood='#5C3A1E', fret='#d0b090', string='#e0c0a0'),
        'Ocean': dict(bg_dark='#0a1520', bg_surface='#0f1d2a', bg_panel='#152535', accent_blue='#44ccee', accent_red='#ee5566', accent_gold='#eebb44', accent_green='#44cc88', accent_purple='#8866ee', accent_orange='#ee8844', text_light='#e0eef8', text_dim='#6688aa', piano_white='#eef5fa', piano_black='#0a1520', wood='#2F4F4F', fret='#90a0b0', string='#a0b0c0'),
    }
    def __init__(self): 
        self._t = dict(self.THEMES['Neon']); self._name = 'Neon'
        
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