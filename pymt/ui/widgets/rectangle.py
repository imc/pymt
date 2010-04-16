'''
Rectangle widget: draw a rectangle of his pos/size
'''


__all__ = ['MTRectangularWidget']

from ..factory import MTWidgetFactory
from widget import MTWidget

class MTRectangularWidget(MTWidget):
    '''A rectangular widget that only propagates and handles
    events if the event was within its bounds.
    '''
    def __init__(self, **kwargs):
        super(MTRectangularWidget, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            super(MTRectangularWidget, self).on_touch_down(touch)
            return True

    def on_touch_move(self, touch):
        if self.collide_point(touch.x, touch.y):
            super(MTRectangularWidget, self).on_touch_move(touch)
            return True

    def on_touch_up(self, touch):
        if self.collide_point(touch.x, touch.y):
            super(MTRectangularWidget, self).on_touch_up(touch)
            return True

MTWidgetFactory.register('MTRectangularWidget', MTRectangularWidget)
