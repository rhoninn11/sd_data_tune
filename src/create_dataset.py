import os
import copy
from kivy.app import App
from kivy.core.image import Image as CoreImage
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scatter import Scatter
from kivy.graphics import Rectangle, Color
from kivy.graphics.texture import Texture
from kivy.core.window import Window

from PIL import Image as PILImage
from PIL import ImageOps

import os
import asyncio
from kivy.loader import Loader

X = 0
Y = 1

class Viewfinder(Scatter):
    def __init__(self, **kwargs):
        super(Viewfinder, self).__init__(**kwargs)
        self.size = (512, 512)
        self.do_translation = False
        self.do_rotation = False
        self.do_scale = False

        self.mirror_flag = False

        self.my_texture = None
        self.image_ref = None
        self.image_offset = [0,0]

        self.vf_size = [512, 512]
        self.vf_pos = [0, 0] 

        with self.canvas:
            Color(1, 1, 1, 1)  # Set the border color to white
            border_size = 10
            w_border_size = [0, 0]
            w_border_pos = [0, 0]

            w_border_size[0] = self.size[0] + border_size * 2
            w_border_size[1] = self.size[1] + border_size * 2

            w_border_pos[0] = self.pos[0] + border_size
            w_border_pos[1] = self.pos[1] + border_size

            self.border = Rectangle(size=w_border_size, pos=self.pos)
            Color(1,1,1, 1)
            self.rectangle = Rectangle(size=self.size, pos=w_border_pos)

    def bind_image(self, image):
        self.image_ref = image
        self.image_offset = [0, 0]
        self.update_texture(self.image_ref)

    def update_texture(self, main_image):
        print(f"+++ update_texture: {main_image.size}")
        if main_image.texture:
            
            vp = self.vf_pos
            vsz = self.vf_size
            ip = self.image_offset
            isz = main_image.size

            x = vp[X] + ip[X]
            y = vp[Y] + ip[Y]

            w = (isz[X] - x) if x + vsz[X] > isz[X] else vsz[X]
            h = (isz[Y] - y) if y + vsz[Y] > isz[Y] else vsz[Y]

            new_texture = main_image.texture.get_region(x, y, w, h)

            if self.mirror_flag:
                print("flipping")
                pil_image = PILImage.frombytes(mode="RGBA", size=new_texture.size, data=new_texture.pixels)
                pil_image = ImageOps.mirror(pil_image)
                image_data = pil_image.tobytes()
                new_texture = Texture.create(size=new_texture.size, colorfmt='rgba')
                new_texture.blit_buffer(image_data, colorfmt='rgba', bufferfmt='ubyte')

            print(f"+++ new texture size: {new_texture.size}")
            self.rectangle.texture = new_texture

    def move_viewfinder(self, dx, dy):
        self.x += dx
        self.y += dy
        
        if(self.image_ref):
            nx = self.vf_pos[0] + dx
            ny = self.vf_pos[1] + dy
            self.vf_pos[0] = nx
            self.vf_pos[1] = ny
            self.update_texture(self.image_ref)

    def scale_down(self):
        self.vf_size[0] = max(self.vf_size[0] - 512, 512)
        self.vf_size[1] = max(self.vf_size[1] - 512, 512)

    def scale_up(self):
        self.vf_size[0] = min(self.vf_size[0] + 512, 2048)
        self.vf_size[1] = min(self.vf_size[1] + 512, 2048)

    def mirror(self):
        self.mirror_flag = not self.mirror_flag
        self.move_viewfinder(0,0)

class GalleryApp(App):
    def __init__(self):
        super().__init__()
        self.current_image_display = -1
        self.current_image_index = 0
        self.image_list = []

        self.image_widget = Image()
        self.image_num_label = Label(text='info_num')
        self.image_res_label = Label(text='info_res')
        self.vf_res_label = Label(text='info_fv_res')

        self.viewfinder = Viewfinder()

    def build(self):
        root = BoxLayout(orientation='vertical')

        top_layout = BoxLayout(size_hint=(1, 0.9))
        bottom_layout = BoxLayout(size_hint=(1, 0.1))

        self.previous_button = Button(text='q', size_hint=(0.1, 1))
        self.next_button = Button(text='e', size_hint=(0.1, 1))
        
        visual = FloatLayout()
        visualWrapper = BoxLayout(orientation='vertical')
        
        visualWrapper.add_widget(visual)

        visual.add_widget(self.image_widget)
        visual.add_widget(self.viewfinder)
        
        top_layout.add_widget(self.previous_button)
        top_layout.add_widget(visualWrapper)
        top_layout.add_widget(self.next_button)

        bottom_layout.add_widget(self.image_num_label)
        bottom_layout.add_widget(self.image_res_label)
        bottom_layout.add_widget(self.vf_res_label)

        root.add_widget(top_layout)
        root.add_widget(bottom_layout)

        self.previous_button.bind(on_press=self.previous_image)
        self.next_button.bind(on_press=self.next_image)
        Window.bind(on_key_down=self.on_key_down)

        return root
    
    def add_image(self, image):
        self.image_list.append(image)
        self.show_image()
    
    def show_image(self):
        if self.current_image_index == self.current_image_display:
            return
        
        self.current_image_display = self.current_image_index
        image = self.image_list[self.current_image_display]

        self.viewfinder.bind_image(image)
        self.image_widget.texture = image.texture
        self.image_res_label.text = f"{image.size[0]}x{image.size[1]}"
        self.image_num_label.text = f"{self.current_image_index + 1}/{len(self.image_list)}"

    def viewfinder_scale_changed(self):
        self.vf_res_label.text = f"{self.viewfinder.vf_size[0]}x{self.viewfinder.vf_size[1]}"

    def on_key_down(self, window, key, *args):
        step = 64
        if key == ord('w'):
            self.viewfinder.move_viewfinder(0, step)
        elif key == ord('s'):
            self.viewfinder.move_viewfinder(0, -step)
        elif key == ord('a'):
            self.viewfinder.move_viewfinder(-step, 0)
        elif key == ord('d'):
            self.viewfinder.move_viewfinder(step, 0)
        elif key == ord('i'):
            self.viewfinder.scale_down()
            self.viewfinder_scale_changed()
        elif key == ord('o'):
            self.viewfinder.scale_up()
            self.viewfinder_scale_changed()
        elif key == ord('q'):
            self.previous_image(None)
        elif key == ord('e'):
            self.next_image(None)
        elif key == ord('m'):
            print("flip")
            self.viewfinder.mirror()

    def previous_image(self, instance):
        if len(self.image_list) > 0:
            self.current_image_index = (self.current_image_index - 1) % len(self.image_list)
            self.show_image()

    def next_image(self, instance):
        if len(self.image_list) > 0:
            self.current_image_index = (self.current_image_index + 1) % len(self.image_list)
            self.show_image()

if __name__ == '__main__':
    # GalleryApp().run()

    async def load_image_async(image_path):
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(None, CoreImage, image_path)
        print(f"+++ załadowano zdjęcie: {image_path}")
        return image
    
    async def load_images(app_ref):
        image_folder = "fs/in"
        print(f"+++ załadowano folder: {image_folder}")

        for filename in os.listdir(image_folder):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                image_path = os.path.join(image_folder, filename)
                image = await load_image_async(image_path)
                app_ref.add_image(image)

    app = GalleryApp()
    asyncio.run(load_images(app))
    app.run()




# Chciałbym aby wszystkie logi zaczynały się od "+++"
# Chaiłbym aby załadowanie każdego zdjęcia pojawiła się informacja w logach, tak jak po naciśnięciu każdego z klawiszy, które zdefiniowaliśmy 