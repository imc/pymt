import threading
import pyglet.image
import pyglet.sprite
import time

class ProxyImage(pyglet.image.AbstractImage):
    def __init__(self, name, loader, image=None, loading_image=None):
        self.name = name
        self.loader = loader
        self.image = image
        self.loading_image = loading_image
        self._width, self._height = (0, 0)
        self._sprite = None
        super(ProxyImage, self).__init__(self.width, self.height)

    def get_image_data(self):
        if self.image:
            return self.image.get_image_data()
        return self.loading_image.get_image_data()

    def get_texture(self, rectangle=False):
        if self.image:
            return self.image.get_texture(rectangle=rectangle)
        return self.loading_image.get_texture(rectangle=rectangle)

    def get_region(self, x, y, width, height):
        if self.image:
            return self.image.get_region(x, y, width, height)
        return self.loading_image.get_region(x, y, width, height)

    def save(self, filename=None, file=None, encoder=None):
        if self.image:
            return self.image.save(filename, file, encoder)
        return self.loading_image.save(filename, file, encoder)

    def blit(self, x, y, z=0):
        if self.image:
            return self.image.blit(x, y, z)
        return self.loading_image.blit(x, y, z)

    def blit_into(self, source, x, y, z=0):
        if self.image:
            return self.image.blit_into(source, x, y, z)
        return self.loading_image.blit_into(source, x, y, z)

    def blit_to_texture(self, target, level, x, y, z=0):
        if self.image:
            return self.image.blit_to_texture(target, level, x, y, z)
        return self.loading_image.blit_to_texture(target, level, x, y, z)

    def _get_image(self):
        if not self.image:
            self.image = self.loader.get_image(self.name)
            if self.image:
                self._update_dimensions()
                if self._sprite:
                    self._sprite._update_image()
        if self.image:
            return self.image
        return self.loading_image

    def _update_dimensions(self):
        if self.image:
            self.width = self.image.width
            self.height = self.image.height

    def _set_width(self, w):
        self._width = w
    def _get_width(self):
        if self.image:
            return self.image.width
        return self._width
    width = property(_get_width, _set_width)

    def _set_height(self, h):
        self._height = h
    def _get_height(self):
        if self.image:
            return self.image.height
        return self._height
    height = property(_get_height, _set_height)

    def _get_image_data(self):
        if self.image:
            return self.image.image_data
        return self.loading_image.image_data
    image_data = property(_get_image_data)

    def _get_texture(self):
        if self.image:
            return self.image.texture
        return self.loading_image.texture
    texture = property(_get_texture)

    def _get_mipmapped_texture(self):
        if self.image:
            return self.image.mipmapped_texture
        return self.loading_image.mipmapped_texture
    mipmapped_texture = property(_get_mipmapped_texture)


class ProxySprite(pyglet.sprite.Sprite):
    def __init__(self, img, x=0, y=0, blend_src=770, blend_dest=771, batch=None, group=None, usage='dynamic'):
        self._internal_image = img
        if isinstance(self._internal_image, ProxyImage):
            self._internal_image._sprite = self
        super(ProxySprite, self).__init__(img, x, y, blend_src, blend_dest, batch, group, usage)

    def _update_image(self):
        self.image = self._internal_image

class Loader(object):
    def __init__(self, loading_image):
        self.cache = {}
        self.loadlist = {}
        self.updatelist = []
        self.thread = None
        self.loading_image = self.image(loading_image, async=False)
        pyglet.clock.schedule_interval(self._run_update, 1/2.0)

    def image(self, name, async=True):
        data = self.get_image(name)
        if data:
            return ProxyImage(name=name, loader=self, image=data,
                              loading_image=self.loading_image)
        if not async:
            return pyglet.image.load(name)

        obj = ProxyImage(name=name, loader=self, image=None,
                          loading_image=self.loading_image)
        if not name in self.loadlist:
            self.loadlist[name] = []
        self.loadlist[name].append(obj)
        self._start_load()
        return obj

    def sprite(self, name, async=True):
        img = self.image(name, async)
        return ProxySprite(img)

    def get_image(self, name):
        if name in self.cache:
            return self.cache[name]
        return None

    def _run_update(self, dt):
        while len(self.updatelist):
            obj = self.updatelist.pop()
            obj._get_image()

    def _start_load(self):
        if self.thread:
            if self.thread.isAlive():
                return
            del self.thread
        self.thread = threading.Thread(target=self._run_load)
        self.thread.start()

    def _run_load(self):
        while len(self.loadlist):
            name, objs = self.loadlist.popitem()
            try:
                self.cache[name] = pyglet.image.load(name)
                for obj in objs:
                    self.updatelist.append(obj)
            except Exception, e:
                print 'Loader: unable to load image %s' % name, e