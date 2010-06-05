'''
Circular Slider: Using this you can make circularly shaped sliders
'''


__all__ = ('MTCircularSlider', 'RangeException')

from OpenGL.GL import glTranslatef, glRotatef
from ...graphx import drawSemiCircle, gx_matrix, set_color, drawLine
from ...vector import Vector
from ..factory import MTWidgetFactory
from widget import MTWidget
from math import cos,sin,radians

class RangeException(Exception):
    pass

class MTCircularSlider(MTWidget):
    '''MTCircularSlider is an implementation of a circular scrollbar using MTWidget.

    ..warning ::
        The widget is drawed from his center. Cause of that, the size of the
        widget will be automaticly adjusted from the radius of the slider.
        Eg: if you ask for a radius=100, the widget size will be 200x200

    :Parameters:
        `min` : int, default is 0
            Minimum value of slider
        `max` : int, default is 100
            Maximum value of slider
        `sweep_angle` : int, default is 90
            The anglular length of the slider you want.
        `value` : int, default is `min`
            Default value of slider
        `thickness` : int, default is 40
            Thickness of the slider
        `radius` : int, default is 200
            Radius of the slider
        `rotation` : int, default is 0
            Start rotation of circle
        `padding` : int
            Padding of content

    :Styles:
        `slider-color` : color
            Color of the slider
        `bg-color` : color
            Background color of the slider

    :Events:
        `on_value_change`
            Fired when slider value is changed
    '''
    def __init__(self, **kwargs):
        kwargs.setdefault('min', 0)
        kwargs.setdefault('max', 100)
        kwargs.setdefault('radius', 200)
        kwargs.setdefault('thickness', 40)
        kwargs.setdefault('padding', 3)
        kwargs.setdefault('sweep_angle', 90)
        kwargs.setdefault('rotation', 0)

        have_size = 'size' in kwargs

        super(MTCircularSlider, self).__init__(**kwargs)

        # register event
        self.register_event_type('on_value_change')

        # privates
        self._last_touch    = (0, 0)
        self._slider_angle  = 0.

        self.radius         = kwargs.get('radius')
        self.rotation       = kwargs.get('rotation')
        self.thickness      = kwargs.get('thickness')
        self.padding        = kwargs.get('padding')
        self.sweep_angle    = kwargs.get('sweep_angle')
        self.min            = kwargs.get('min')
        self.max            = kwargs.get('max')
        self._value         = self.min
        self._scale = (self.max - self.min) / float(360)

        if not self.min < self.max:
            raise(Exception('min >= max'))
        if not self.sweep_angle > 0:
            raise(Exception('sweep_angle <= 0'))
        if not self.sweep_angle <= 360:
            raise(Exception('sweep_angle > 360'))
            
        if kwargs.get('value') != None:
            self._set_value(kwargs.get('value'))
        self.touchstarts    = []

    def collide_point(self, x, y):
        #A algorithm to find the whether a touch is within a semi ring
        point_dist = Vector(self.center).distance((x, y))
        point_angle = Vector(self.radius_line).angle((x - self.center[0], y - self.center[1]))
        if point_angle < 0:
            point_angle = 360. + point_angle
        if 0 < point_angle > self.sweep_angle:
            return False
        return self.radius - self.thickness < point_dist <= self.radius

    def on_value_change(self, value):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            self.touchstarts.append(touch.id)
            self.last_touch = (touch.x - self.center[0], touch.y - self.center[1])
            self._value = (self.slider_fill_angle) * (self.max - self.min) / self.sweep_angle + self.min
            self._calculate_angle()
            return True

    def on_touch_move(self, touch):
        if self.collide_point(touch.x, touch.y) and touch.id in self.touchstarts:
            self.last_touch = (touch.x - self.center[0], touch.y - self.center[1])
            self._value = (self.slider_fill_angle) * (self.max - self.min) / self.sweep_angle + self.min
            self._calculate_angle_from_touch()
            return True

    def _calculate_angle_from_touch(self):
        self.angle = Vector(self.radius_line).angle(self.last_touch)
        self._calculate_angle()

    def _calculate_angle(self):
        if self.angle<0:
            self.slider_fill_angle = self.angle+360
        else:
            self.slider_fill_angle = self.angle
        self.dispatch_event('on_value_change', self._value)

    def on_draw(self):
        with gx_matrix:
            set_color(*self.style.get('bg-color'))
            glTranslatef(x, y, 0)
            glRotatef(-self.rotation, 0, 0, 1)
            drawSemiCircle((self.size[0]/2,self.size[1]/2),self.radius-self.thickness,self.radius,32,1,0,self.sweep_angle)
            set_color(*self.style.get('slider-color'))
            drawSemiCircle((self.size[0]/2,self.size[1]/2),self.radius-self.thickness+self.padding,self.radius-self.padding,32,1,0,self.slider_fill_angle)

    def _get_value(self):
        return self._value
    def _set_value(self,value):
        if value >= self.min and value <= self.max:
            self._value = value
            self.angle = float(value - self.min) / (float(self.max - self.min) / float(self.sweep_angle))
            self._calculate_angle()
    value = property(_get_value, _set_value, doc='Sets the current value of the slider')

MTWidgetFactory.register('MTCircularSlider', MTCircularSlider)
