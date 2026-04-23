class Localization:
    def __init__(self, width: int = 5, height: int = 5):
        self.width = width
        self.height = height
        self.positions = []

        self._generate_snake_path()
        self.index = 0

    def _generate_snake_path(self):
        self.positions.clear()

        for y in range(1, self.height + 1):
            if y % 2 == 1:
                for x in range(1, self.width + 1):
                    self.positions.append((x, y))
            else:
                for x in reversed(range(1, self.width + 1)):
                    self.positions.append((x, y))

    def get_position(self):
        if self.index >= len(self.positions):
            self.index = 0

        pos = self.positions[self.index]
        self.index += 1
        return pos

    def reset(self):
        self.index = 0

    def get_all_positions(self):
        return self.positions.copy()


if __name__ == "__main__":
    loc = Localization(width=5, height=5)
    print(loc.get_all_positions())