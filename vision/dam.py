"""

Dam is used to provide an abstraction data structure to solve the autonomous driving task.

** Functionality **

By importing the module you gain access to a number of classes, each representing different components of the dam.

The 'Dam' class provides the highest level of abstraction to represent a grid of squares. It provides a simple function
to mark a crack at a given position, where the position's default value is the position of currently viewed square. The
dam is printable, and presents a grid of squares with the lengths of cracks in them. The grid is indexed as follows:

|  0  |  1  |  2  |  3  |
|  4  |  5  |  6  |  7  |
|  8  |  9  | 10  | 11  |

The 'Square' class is used to maintain information about cracks' positions, by remember if a crack is in it or not.

The 'Crack' class carries information about the length of a crack, and supports error-checking against requirements.

** Example **

Let dam = Dam(). To mark a crack of length 21.3 at the current position, call:

    dam.position = 0
    dam.mark_crack(21.3)

Notice that without specifying the position, a 'TypeError' would be raised. The result of printing dam is as follows:

    |  20   |   X   |   X   |   X   |
    |   X   |   X   |   X   |   X   |
    |   X   |   X   |   X   |   X   |

Notice that the actual value registered is 20, due to the competition's requirements for a crack (max length is 20).

** Author **

Kacper Florianski

"""


class Dam:

    def __init__(self):
        """

        Function used to initialise full dam's representation.

        """

        # Initialise a list of squares. Indexing is in form (column - 1) + 4*(row - 1)
        self._squares = [Square(i) for i in range(12)]

        # Initialise the current position on the map, None if no start point initialised
        self._position = None

        # Initialise the start and end shapes - these will be provided by the competition judge
        self.start_shape, self.end_shape = None, None

    def mark_crack(self, length: float, *, position=None):
        """

        Function used to save the crack onto a grid.

        :param length: Length of the crack.
        :param position: Grid position. Check indexing in module's docstrings to understand better.

        """

        # Handle the default position
        if position is None:

            # Check if the position has been assigned
            if self._position is not None:
                position = self._position

        # Add a crack to the square at the given position if it didn't contain one
        if self._squares[position].crack is None:
            self._squares[position].crack = length

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, value):

        # Check if the value specified is between 0 and 12 inclusive
        if value in range(13):
            self._position = value
        else:
            raise ValueError("Position index must be between 0 and 12 inclusive")

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
        """

        Function used to initialise the dam's grid component.

        :param position: Grid position. Check indexing in module's docstrings to understand better.

        """

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
        """

        Function used to initialise a crack.

        :param length: Length of the crack

        """

        # Declare and initialise variables related to the length of the crack
        self._length, self.LENGTH_MAX, self.LENGTH_MIN = length, 20, 8

        # Fix any invalid length readings and adjust formatting
        self._format_length()

    @property
    def length(self):
        return self._length

    def _format_length(self):
        """

        Function used to restrict the length by the competition's requirements.

        Precisely, the restrictions are on the maximum length, minimum length, and the number of digits after the coma.

        """

        # Format the length to meet the requirements / restrictions of the competition
        self._length = max(self._length, self.LENGTH_MIN)
        self._length = min(self._length, self.LENGTH_MAX)
        self._length = round(self._length, 1)
