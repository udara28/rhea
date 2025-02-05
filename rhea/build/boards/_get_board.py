# Copyright (c) 2014 Christopher Felton
#

from __future__ import division
from __future__ import print_function

from .xilinx._xula import Xula, Xula2
from .xilinx._papilio import Pone
from .xilinx._anvyl import Anvyl
from .xilinx._mojo import Mojo

from .altera._de0nano import DE0Nano
from .altera._de0nano_soc import DE0NanoSOC

from .lattice._icestick import Icestick
from .lattice._catboard import CATBoard


xbrd = {
    'xula': Xula,
    'xula2': Xula2,
    'pone': Pone,
    'anvyl': Anvyl,
    'mojo': Mojo
}

abrd = {
    'de0nano': DE0Nano,
    'de0nano_soc': DE0NanoSOC,
}

lbrd = {
    'icestick': Icestick,
    'catboard': CATBoard
}


def get_board(name):
    """ retrieve a board definition from the name provided.
    """
    brd = None
    if name in xbrd:
        brd = xbrd[name]()
    elif name in abrd:
        brd = abrd[name]()
    elif name in lbrd:
        brd = lbrd[name]()
    else:
        # @todo: print out a list of boards and descriptions
        raise ValueError("Invalid board %s"%(name,))

    return brd


def get_all_board_names():
    return list(xbrd.keys()) + list(abrd.keys()) + list(lbrd.keys())
