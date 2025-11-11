class Aircraft:
    def __init__(self, aircraft_id):
        self.id = aircraft_id
        self.position = 0

    def move(self):
        self.position += 1
        return f"Aircraft {self.id} at position {self.position}"
