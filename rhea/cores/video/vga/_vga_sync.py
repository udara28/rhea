
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from myhdl import *

from ._timing_params import calc_timings


def vga_sync(
    # [ports and interfaces}
    glbl,  # global bundle of signals, clock, reset
    vga,   # signals for the VGA
    vmem,  # the video memory interface

    # [parameters]
    resolution=(640, 480,),  # resolution in pixels
    refresh_rate=60,         # refresh rate in Hz (vertical rate)
    line_rate=31250          # line rate in Hz (horizontal rate)
    ):
    """
    The following is the generation of the signals required 
    to drive a VGA display.  This implementation is derived
    from the pseudo code provide here:
    http://hamsterworks.co.nz/mediawiki/index.php/Module_11
    
    Well isn't that nice - the Python/MyHDL implementation is 
    very close to the "pseudo code"!

    Also, this module is intended to be parameterizable and
    modular based on the desired video settings
       clock.frequency - the clock used to generate the pixel
                         clock
                         
       video_resolution - in pixels, tVGA resolution
       refresh_rate     - in Hz, default 60
       line_rate        - in Hz, default is 31,250

    Ports (arguments):
    ------------------
      glbl.clock : system synchronous clock
      glbl.reset : system reset
      
      vga.hsync : horizontal sync
      vga.vsync : vertical sync
      vga.red   : 
      vga.green :
      vga.blue  :
      
      vmem.hpxl : horizontal pixel address
      vmem.vpxl : vertical pixel address
      vmem.red   : red pixel value
      vmem.green : green pixel value
      vmem.blue  : blue pixel value
   
    Parameters:
    -----------
      resolution   : video resolution
      refresh_rate : vertical rate in Hz
      line_rate    : horizontal rate in Hz 
    
    VGA Timing
    ----------
    """
    res = resolution
    clock = glbl.clock
    reset = glbl.reset

    # compute the limits (counter limits) for the vsync
    # and hsync timings.  Review the calc_timing function
    # for definitions of A,B,C,D,E,F,P,Q,R,S, and Z
    (A,B,C,D,E,F,
     P,Q,R,S,X,Z,) = calc_timings(clock.frequency, resolution,
                                  refresh_rate, line_rate)
    # full_screen pixels res[0]*res[1] (should be)
    full_screen = F

    # counters to count the pixel clock (clock)
    HPXL, VPXL = res
    xcnt = intbv(0, min=-1, max=X+1)  # clock div
    hcnt = intbv(0, min=0, max=A+1)   # hor count in ticks
    vcnt = intbv(0, min=0, max=F+1)   # ver count in ticks

    # local references to interface signals
    hpxl = vmem.hpxl
    vpxl = vmem.vpxl

    # debug stuff
    hcd = Signal(hcnt)  # trace horizontal count
    vcd = Signal(vcnt)  # trace vertical count

    # the hsync and vsync are periodic so we can start anywhere,
    # it is convenient to start at the active pixel area
    @always_seq(clock.posedge, reset=reset)
    def rtl_sync():    
        # horizontal and vertical counters
        hcnt[:] = hcnt + 1
        if vcnt == full_screen:
            vcnt[:] = 0
            hcnt[:] = 0
        elif vcnt > R:
            hcnt[:] = A-1
        elif hcnt >= A:
            hcnt[:] = 0
            vcnt[:] = vcnt + 1

        # clock divider for pixel enable
        xcnt[:] = xcnt + 1
        if hcnt == 1:
            xcnt[:] = 1
        elif xcnt == X:
            xcnt[:] = 0
        
        # tick counter to generate pixel enable
        if xcnt == 0 and hcnt <= D:
            vga.pxlen.next = True
        else:
            vga.pxlen.next = False

        # generate the VGA strobes
        if hcnt >= (D+E) and hcnt < (D+E+B):
            vga.hsync.next = False
        else:
            vga.hsync.next = True
            
        if vcnt >= (R+S) and  vcnt < (R+S+P):
            vga.vsync.next = False
        else:
            vga.vsync.next = True

        # current pixel x,y coordinates
        if hpxl < (HPXL-1) and xcnt == 0 and hcnt <= D:
            hpxl.next = hpxl + 1
        elif hcnt > (D+E):
            hpxl.next = 0

        if hcnt >= (A-1) and vcnt < (R-1):
            vpxl.next = vpxl + 1
        elif vcnt > (R+S):
            vpxl.next = 0
        
        # debug and verification
        hcd.next = hcnt
        vcd.next = vcnt
        # end debug stuff

    # logically define which VGA state currently in.  This is 
    # required for (simplified) verification but will be removed
    # by synthesis (outputs dangling)
    @always_comb
    def rtl_state():
        if not vga.hsync:
            vga.state.next = vga.States.HSYNC
        elif not vga.vsync:
            vga.state.next = vga.States.VSYNC
        elif hcd < D:
            vga.state.next = vga.States.ACTIVE
        elif vcd >= R and vcd < (R+S):
            vga.state.next = vga.States.VER_FRONT_PORCH        
        elif vcd >= (R+S) and vcd < (R+S+P):
            pass # should be handled by above
        elif vcd >= (R+S+P) and vcd < (full_screen):
            vga.state.next = vga.States.VER_BACK_PORCH
        elif hcd >= D and hcd < (D+E):
            vga.state.next = vga.States.HOR_FRONT_PORCH
        elif hcd >= (D+E) and hcd < (D+E+B):
            pass # should be handled by above
        elif hcd >= (D+E+B) and hcd < (D+E+B+C):
            vga.state.next = vga.States.HOR_BACK_PORCH

        if hcd < D:
            vga.active.next = True
        else:
            vga.active.next = False

    #_state = Signal(intbv(0)[8:])
    #@always_comb
    #def tmon():
    #    _state.next = int(vga.state._val._index)

    # map the video memory pixels to the VGA bus
    @always_comb
    def rtl_map():
        vga.red.next = vmem.red
        vga.green.next = vmem.green
        vga.blue.next = vmem.blue

    return rtl_sync, rtl_state, rtl_map
