import os
import glob
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Rectangle
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.loader import Loader
from PIL import Image as PilImage

INPUT_PATH = 'fs/in'
OUTPUT_PATH = 'fs/out'
VIEWFINDER_SIZE = [512, 1024, 1536, 2048]
VIEWFINDER_STEP = 64
IMAGE_SIZES = (512, 1024, 1536, 2048)
WINDOW_SIZE = (800, 600)

Window.size = WINDOW_SIZE

class PhotoViewer(BoxLayout):
    image_source = StringProperty('')
    viewfinder_source = StringProperty('')
    viewfinder_pos = ListProperty([0, 0])
    image_index = NumericProperty(0)
    image_count = NumericProperty(0)
    image_size = ListProperty([0, 0])
    viewfinder_size_index = NumericProperty(0)
    viewfinder_size = ListProperty(VIEWFINDER_SIZE[0])
    photos_taken = NumericProperty(0)

    def __init__(self, **kwargs):
        super(PhotoViewer, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.images = sorted(glob.glob(os.path.join(INPUT_PATH, '*')))
        self.image_count = len(self.images)
        self.load_image(self.images[self.image_index])
        self.bind(viewfinder_pos=self.update_viewfinder_texture)
        Window.bind(on_key_down=self.on_key_down)

    def on_key_down(self, window, key, *args):
        if key == 'q':
            self.previous_image()
        elif key == 'e':
            self.next_image()
        elif key in ('w', 's', 'a', 'd'):
            self.move_viewfinder(key)
        elif key == 'i':
            self.decrease_viewfinder_size()
        elif key == 'o':
            self.increase_viewfinder_size()
        elif key == 'm':
            self.flip_image()
        elif key == 'x':
            self.take_photo()

    def load_image(self, path):
        self.image_source = path
        pil_image = PilImage.open(path)
        self.image_size = pil_image.size

    def previous_image(self):
        if self.image_index > 0:
            self.image_index -= 1
            self.load_image(self.images[self.image_index])

    def next_image(self):
        if self.image_index < (self.image_count - 1):
            self.image_index += 1
            self.load_image(self.images[self.image_index])

    def move_viewfinder(self, direction):
        if direction == 'w':
            self.viewfinder_pos[1] += VIEWFINDER_STEP
        elif direction == 's':
            self.viewfinder_pos[1] -= VIEWFINDER_STEP
        elif direction == 'a':
            self.viewfinder_pos[0] -= VIEWFINDER_STEP
        elif direction == 'd':
            self.viewfinder_pos[0] += VIEWFINDER_STEP

    def decrease_viewfinder_size(self):
        if self.viewfinder_size_index > 0:
            self.viewfinder_size_index -= 1
            self.viewfinder_size = VIEWFINDER_SIZE[self.viewfinder_size_index]

    def increase_viewfinder_size(self):
        if self.viewfinder_size_index < len(VIEWFINDER_SIZE) - 1:
            self.viewfinder_size_index += 1
            self.viewfinder_size = VIEWFINDER_SIZE[self.viewfinder_size_index]

    def flip_image(self):
        with self.canvas:
            self.ids['image'].texture.flip_horizontal()

    def update_viewfinder_texture(self, *args):
        pil_image = PilImage.open(self.image_source).crop((
            self.viewfinder_pos[0],
            self.viewfinder_pos[1],
            self.viewfinder_pos[0] + self.viewfinder_size[0],
            self.viewfinder_pos[1] + self.viewfinder_size[1],
        ))
        pil_image.thumbnail((512, 512))
        img_data = pil_image.tobytes()
        viewfinder_texture = Image(source=self.image_source).texture
        viewfinder_texture.blit_buffer(img_data, colorfmt='rgba', bufferfmt='ubyte')
        self.viewfinder_source = viewfinder_texture

    def take_photo(self):
        self.photos_taken += 1
        output_filename = os.path.join(OUTPUT_PATH, f'output_{self.photos_taken:04d}.png')
        viewfinder_texture = self.ids['viewfinder'].texture
        viewfinder_texture.save(output_filename)

class MyApp(App):
  def build(self):
    return PhotoViewer()  

if name == 'main':
  MyApp().run()