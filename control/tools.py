def normalise(value, current_min, current_max, intended_min, intended_max):
    """

    Function used to normalise a value to fit within a given range, knowing its actual range. MinMax normalisation.

    :param value: Value to be normalised
    :param current_min: The actual minimum of the value
    :param current_max: The actual maximum of the value
    :param intended_min: The expected minimum of the value
    :param intended_max: The expected maximum of the value
    :return: Normalised value

    """
    return intended_min + (value - current_min) * (intended_max - intended_min) / (current_max - current_min)