from flags import Flags

class PositionElgibility(Flags):
    """ Bitwise enum for marking a player's egibility.abs
    """

    catcher = ()
    first_base = ()
    second_base = ()
    third_base = ()
    short_stop = ()
    outfield = ()
    left_field = ()
    center_field = ()
    right_field = ()
    designated_hitter = ()
    pitcher = ()
    starting_pitcher = ()
    relief_pitcher = ()