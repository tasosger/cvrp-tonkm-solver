class Saving:
    def __init__(self, n1, n2, sav):
        self.n1 = n1
        self.n2 = n2
        self.score = sav
    
    def __lt__(self, other):
        return self.score > other.score
