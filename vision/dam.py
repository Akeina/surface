class Dam:

    def __init__(self):

        # Initialise a list of squares. Indexing is in form (column - 1) + 4*(row - 1)
        self._squares = [Square(i) for i in range(12)]

        # Initialise the current position on the map, -1 if no start point initialised
        self._position = -1

        # Initialise the start and end shapes - these will be provided by the competition judge
        self.start_shape, self.end_shape = None, None

    def mark_crack(self, length: float):

        # Add a crack to the square at current position if it didn't contain one
        if self._squares[self._position].crack is None:
            self._squares[self._position].crack = length

    def __str__(self):

        # Declare a helper variable to store information about each row
        representation = list()

        # Iterate over each row and add formatted crack information
        for i in range(1, 4):
            representation.append("| {0[0]:^5} | {0[1]:^5} | {0[2]:^5} | {0[3]:^5} |".format(
                [square.crack if square.crack is not None else "X" for square in self._squares[4 * (i - 1):4 * i]]))

        # Return the dam's string representation
        return "\n".join(representation)


class Square:

    def __init__(self, position: int):

        # Initialise base
        self.width, self.height = 30, 30

        # Initialise the crack information to remember which crack is in which square
        self._crack = None

        # Initialise the square's position on the grid
        self._position = position

    @property
    def crack(self):
        return self._crack and self._crack.length

    @crack.setter
    def crack(self, length: float):
        self._crack = Crack(length)


class Crack:

    def __init__(self, length: float):

        # Declare and initialise variables related to the length of the crack
        self._length, self.LENGTH_MAX, self.LENGTH_MIN = length, 20, 8

        # Fix any invalid length readings and adjust formatting
        self._format_length()

    @property
    def length(self):
        return self._length

    def _format_length(self):

        # Format the length to meet the requirements / restrictions of the competition
        self._length = max(self._length, self.LENGTH_MIN)
        self._length = min(self._length, self.LENGTH_MAX)
        self._length = round(self._length, 1)
