'''
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Object part by Felipe Carvalho
'''

import osc
import pyglet
from pyglet.gl import *

import pymt
import sys, getopt, os
from Queue import Queue
from threading import Lock


#global to this module.  all event listeners will add themselves to this
# list upon creation
tuio_event_q = Queue()
touch_event_listeners = []
TUIO_listeners = []

def intersection(set1, set2):
    return filter(lambda s:s in set2, set1)

def difference(set1, set2):
    return filter(lambda s:s not in set2, set1)

class Tuio2DCursor(object):

    def __init__(self, blobID, args):
        self.blobID = blobID
        self.oxpos = self.oypos = 0.0
        self.depack(args)
	self.motcalc()

    def move(self, args):
        self.oxpos, self.oypos = self.xpos, self.ypos
        self.depack(args)
	self.motcalc()

    def motcalc(self):
	#NOTE: This does not work with the mouse, but with a real TUIO stream it does
	'''Calculates the relative movement if the tracker is not providing it'''
	'''Ported from touchpy'''
	self.xmot = self.xpos - self.oxpos
	self.ymot = self.ypos - self.oypos

    def depack(self, args):
        if len(args) < 5:
            self.xpos, self.ypos = args[0:2]
        elif len(args) == 5:
            self.xpos, self.ypos, self.xmot, self.ymot, self.mot_accel = args[0:5]
        else:
            self.xpos, self.ypos, self.xmot, self.ymot, self.mot_accel, self.Width , self.Height = args[0:7]


class Tuio2DObject(object):

    def __init__(self, blobID, args):
        self.blobID = blobID
        self.oxpos = self.oypos = 0.0
        self.depack(args)

    def move(self, args):
        self.oxpos, self.oypos = self.xpos, self.ypos
        self.depack(args)
	self.motcalc()

    def motcalc(self):
	'''Calculates the relative movement if the tracker is not providing it'''
	'''Ported from touchpy'''
	self.xmot = self.xpos - self.oxpos
	self.ymot = self.ypos - self.oypos
	print 'foo'

    def depack(self, args):
        if len(args) < 5:
            self.xpos, self.ypos = args[0:2]
        elif len(args) == 9:
            self.id, self.xpos, self.ypos, self.angle, self.Xvector, self.Yvector,self.Avector, self.xmot, self.ymot, = args[0:9]
        else:
            self.id, self.xpos, self.ypos, self.angle, self.Xvector, self.Yvector,self.Avector, self.xmot, self.ymot, self.Width , self.Height = args[0:11]




'''
In TUIOGetter , The "type" item differentiates the 2Dobj of the 2DCur , to choose
the  righ parser on the idle function

'''

class TUIOGetter(object):

    def __init__(self,  host='127.0.0.1', port=3333):
		global TUIO_listeners
		TUIO_listeners.append(self)
		self.host = host
		self.port = port
		self.startListening()

    def startListening(self):
        #print "starting ", self
        osc.init()
        osc.listen(self.host, self.port)
        osc.bind(self.osc_2dcur_Callback, '/tuio/2Dcur')
        osc.bind(self.osc_2dobj_Callback, '/tuio/2Dobj')

    def stopListening(self):
		#print "stopping ", self
		osc.dontListen()

    def close(self):
        osc.dontListen()
        TUIO_listeners.remove(self)

    def osc_2dcur_Callback(self, *incoming):
        global tuio_event_q
        message = incoming[0]
        type, types, args = message[0], message[1], message[2:]
        tuio_event_q.put([type, args, types])

    def osc_2dobj_Callback(self, *incoming):
        global tuio_event_q
        message = incoming[0]
        type, types, args = message[0], message[1], message[2:]
        tuio_event_q.put([type,args, types])


class TouchEventLoop(pyglet.app.EventLoop):

    def __init__(self, host='127.0.0.1', port=3333):
        pyglet.app.EventLoop.__init__(self)
        self.current_frame = self.last_frame = 0
        self.alive2DCur = []
        self.alive2DObj = []
        self.blobs2DCur = {}
        self.blobs2DObj = {}
        self.parser = TUIOGetter(host = host, port = port)

    def close(self):
        if not self.parser:
            return
        self.parser.close()
        self.parser = None

    def parse2dCur(self, args, types):
        global touch_event_listeners
        if args[0] == 'alive':
            touch_release = difference(self.alive2DCur,args[1:])
            touch_down = difference(self.alive2DCur,args[1:])
            touch_move = intersection(self.alive2DCur,args[1:])
            self.alive2DCur = args[1:]
            for blobID in touch_release:
                for l in touch_event_listeners:
                    l.dispatch_event('on_touch_up', self.blobs2DCur, blobID, self.blobs2DCur[blobID].xpos * l.width, l.height - l.height*self.blobs2DCur[blobID].ypos)
                    del self.blobs2DCur[blobID]

        elif args[0] == 'set':
            blobID = args[1]
            if blobID not in self.blobs2DCur:
                self.blobs2DCur[blobID] = Tuio2DCursor(blobID,args[2:])
                for l in touch_event_listeners:
                    l.dispatch_event('on_touch_down', self.blobs2DCur, blobID, self.blobs2DCur[blobID].xpos * l.width, l.height - l.height*self.blobs2DCur[blobID].ypos)

            else:
                self.blobs2DCur[blobID].move(args[2:])
                for l in touch_event_listeners:
                    l.dispatch_event('on_touch_move', self.blobs2DCur, blobID, self.blobs2DCur[blobID].xpos * l.width, l.height - l.height*self.blobs2DCur[blobID].ypos)

    def parse2dObj(self, args, types):
        global touch_event_listeners

        if not args[0] in ['alive', 'set']:
            return

        if args[0] == 'alive':
            touch_release = difference(self.alive2DObj,args[1:])
            touch_down = difference(self.alive2DObj,args[1:])
            touch_move = intersection(self.alive2DObj,args[1:])
            self.alive2DObj = args[1:]

            for blobID in touch_release:
                for l in touch_event_listeners:
                    l.dispatch_event('on_object_up', self.blobs2DObj, blobID,self.blobs2DObj[blobID].id ,self.blobs2DObj[blobID].xpos * l.width, l.height - l.height*self.blobs2DObj[blobID].ypos,self.blobs2DObj[blobID].angle)
                    del self.blobs2DObj[blobID]

        elif args[0] == 'set':
            blobID = args[1]
            if blobID not in self.blobs2DObj:
                self.blobs2DObj[blobID] = Tuio2DObject(blobID,args[2:])
                for l in touch_event_listeners:
                    l.dispatch_event('on_object_down', self.blobs2DObj, blobID, self.blobs2DObj[blobID].id,self.blobs2DObj[blobID].xpos * l.width, l.height - l.height*self.blobs2DObj[blobID].ypos, self.blobs2DObj[blobID].angle)
            else:
                self.blobs2DObj[blobID].move(args[2:])
                for l in touch_event_listeners:
                    l.dispatch_event('on_object_move', self.blobs2DObj, blobID, self.blobs2DObj[blobID].id, self.blobs2DObj[blobID].xpos * l.width, l.height - l.height*self.blobs2DObj[blobID].ypos, self.blobs2DObj[blobID].angle)


    def idle(self):
        global tuio_event_q
        pyglet.clock.tick()
        while not tuio_event_q.empty():
            type,args, types = tuio_event_q.get()
            if type == '/tuio/2Dcur':
                self.parse2dCur(args, types)
            if type == '/tuio/2Dobj':
                self.parse2dObj(args, types)

        for window in pyglet.app.windows:
            window.dispatch_events()
            window.dispatch_event('on_draw')
            window.flip()

        return 0

def stopTUIO():
   global TUIO_listeners
   for listener in TUIO_listeners:
      listener.stopListening()

def startTUIO():
   global TUIO_listeners
   for listener in TUIO_listeners:
      listener.startListening()

#any window that inherhits this or an instance will have event handlers triggered on TUIO touch events
class TouchWindow(pyglet.window.Window):

    def __init__(self, config=None):
        pyglet.window.Window.__init__(self, config=config)
        self.register_event_type('on_touch_up')
        self.register_event_type('on_touch_move')
        self.register_event_type('on_touch_down')

        self.register_event_type('on_object_up')
        self.register_event_type('on_object_move')
        self.register_event_type('on_object_down')

        touch_event_listeners.append(self)


    def on_touch_down(self, touches, touchID, x, y):
        pass

    def on_touch_move(self, touches, touchID, x, y):
        pass

    def on_touch_up(self, touches, touchID, x, y):
        pass

    def on_object_down(self, touches, touchID,id, x, y,angle):
        pass

    def on_object_move(self, touches, touchID,id, x, y,angle):
        pass

    def on_object_up(self, touches, touchID,id, x, y,angle):
        pass


def pymt_usage():
    '''PyMT Usage: %s [OPTION...]

  -h, --help                        prints this mesage
  -f, --fullscreen                  force run in fullscreen
  -w, --windowed                    force run in window
  -p, --port=x                      specify TUIO port (default 3333)
  -H, --host=xxx.xxx.xxx.xxx        specify TUIO host (default 127.0.0.1)
  -F, --fps                         show fps in window
      --dump-frame                  dump each frame in file
      --dump-prefix                 specify a prefix for each frame file
      --dump-format                 specify a format for dump
    '''
    print pymt_usage.__doc__ % (os.path.basename(sys.argv[0]))


def runTouchApp():
    '''Static main function that starts the application loop'''

    # Check if we show event stats
    if pymt.options.get('eventstats'):
        pymt.widget.event_stats_activate()

    host = pymt.options.get('host')
    port = pymt.options.get('port')
    print 'Notice: listening for TUIO on port', port, 'of host', host
    evloop = TouchEventLoop(host=host, port=port)

    try:
        evloop.run()
    except:
        evloop.close()
        raise

    # Show event stats
    if pymt.options.get('eventstats'):
        pymt.widget.event_stats_print()

#a very simple test
if __name__ == '__main__':

    from graphx import *
    touchPositions = {}
    crosshair = pyglet.sprite.Sprite(pyglet.image.load('crosshair.png'))
    crosshair.scale = 0.6

    w = TouchWindow()
    #    w.set_fullscreen()
    @w.event
    def on_touch_down(touches, touchID, x,y):
        touchPositions[touchID] = [(touchID,x,y)]
    @w.event
    def on_touch_up(touches, touchID,x,y):
        del touchPositions[touchID]
    @w.event
    def on_touch_move(touches, touchID, x, y):
        touchPositions[touchID].append((x,y))
    @w.event
    def on_draw():
        w.clear()
        for p in touchPositions:
            touchID,x,y = touchPositions[p][0]
            for pos in touchPositions[p][1:]:
                x, y = pos
                crosshair.x = x
                crosshair.y = y
                crosshair.draw()

    runTouchApp()

tuio_event_q.join()
