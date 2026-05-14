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
            third = (iv[(i+2)%len(iv)]-interval)%12
            fifth = (iv[(i+4)%len(iv)]-interval)%12
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