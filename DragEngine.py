#Version 0.0.1
#Date of update: 08/12/2024

import tkinter as tk
import time
import math
import random

class GraphicsEngine:
    def __init__(self, width, height, title="Graphics Engine"):
        self.width = width
        self.height = height
        self.root = tk.Tk()
        self.root.title(title)
        self.canvas = tk.Canvas(self.root, width=self.width, height=self.height, bg="black")
        self.canvas.pack()

        self.scene_objects = []
        self.running = True
        self.light_source = (0, 200, 0)

        self.camera_x = 0
        self.camera_y = 0
        self.camera_z = -500
        self.camera_pitch = 0
        self.camera_yaw = 0

        self.keys = set()
        self.mouse_dragging = False
        self.last_mouse_x = 0
        self.last_mouse_y = 0

        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

    def on_key_press(self, event):
        self.keys.add(event.keysym)

    def on_key_release(self, event):
        self.keys.discard(event.keysym)

    def on_mouse_press(self, event):
        self.mouse_dragging = True
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y

    def on_mouse_drag(self, event):
        if self.mouse_dragging:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.camera_yaw += dx * 0.1
            self.camera_pitch -= dy * 0.1
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y

    def on_mouse_release(self, event):
        self.mouse_dragging = False

    def add_object(self, obj):
        self.scene_objects.append(obj)

    def remove_object(self, obj):
        if obj in self.scene_objects:
            self.scene_objects.remove(obj)

    def clear_scene(self):
        self.scene_objects = []

    def render_skybox(self):
        for y in range(self.height):
            t = y / self.height
            if t < 0.5:
                color = self.interpolate_color((0, 0, 128), (0, 128, 255), t * 2)
            else:
                color = self.interpolate_color((0, 128, 255), (0, 0, 0), (t - 0.5) * 2)
            self.canvas.create_line(0, y, self.width, y, fill=color)

    @staticmethod
    def interpolate_color(color1, color2, t):
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        return f"#{r:02x}{g:02x}{b:02x}"

    def project_3d_to_2d(self, x, y, z):
        x -= self.camera_x
        y -= self.camera_y
        z -= self.camera_z

        cos_yaw = math.cos(math.radians(self.camera_yaw))
        sin_yaw = math.sin(math.radians(self.camera_yaw))
        cos_pitch = math.cos(math.radians(self.camera_pitch))
        sin_pitch = math.sin(math.radians(self.camera_pitch))

        xz = x * cos_yaw - z * sin_yaw
        z = x * sin_yaw + z * cos_yaw
        yx = y * cos_pitch - z * sin_pitch
        z = y * sin_pitch + z * cos_pitch
        x, y = xz, yx

        if z == 0:
            z = 0.01
        scale = 500 / (z + 500)
        screen_x = x * scale + self.width / 2
        screen_y = -y * scale + self.height / 2
        return screen_x, screen_y

    def calculate_lighting(self, normal):
        lx, ly, lz = self.light_source
        nx, ny, nz = normal
        length = math.sqrt(lx**2 + ly**2 + lz**2)
        dot = max((lx * nx + ly * ny + lz * nz) / (length or 1), 0)
        brightness = int(255 * dot)
        return f"#{brightness:02x}{brightness:02x}{brightness:02x}"

    def main_loop(self):
        while self.running:
            start_time = time.time()

            if "w" in self.keys:
                self.camera_z += 10
            if "s" in self.keys:
                self.camera_z -= 10
            if "a" in self.keys:
                self.camera_x -= 10
            if "d" in self.keys:
                self.camera_x += 10
            if "space" in self.keys:
                self.camera_y += 10
            if "Shift_L" in self.keys:
                self.camera_y -= 10

            for obj in self.scene_objects:
                if hasattr(obj, 'update'):
                    obj.update()

            self.canvas.delete("all")
            self.render_skybox()

            for obj in self.scene_objects:
                if hasattr(obj, 'render'):
                    obj.render(self.canvas, self)

            self.root.update()
            time.sleep(max(1/60 - (time.time() - start_time), 0))

    def stop(self):
        self.running = False

class GameObject:
    def __init__(self, vertices, faces, color="white"):
        self.vertices = vertices
        self.faces = faces
        self.color = color

    def update(self):
        pass

    def render(self, canvas, engine):
        transformed_vertices = [engine.project_3d_to_2d(*v) for v in self.vertices]
        for face in self.faces:
            points = [transformed_vertices[i] for i in face]
            flat_points = [p for point in points for p in point]

            v1 = self.vertices[face[1]]
            v2 = self.vertices[face[2]]
            v0 = self.vertices[face[0]]
            normal = (
                (v1[1] - v0[1]) * (v2[2] - v0[2]) - (v1[2] - v0[2]) * (v2[1] - v0[1]),
                (v1[2] - v0[2]) * (v2[0] - v0[0]) - (v1[0] - v0[0]) * (v2[2] - v0[2]),
                (v1[0] - v0[0]) * (v2[1] - v0[1]) - (v1[1] - v0[1]) * (v2[0] - v0[0]),
            )

            color = engine.calculate_lighting(normal)
            canvas.create_polygon(flat_points, outline=self.color, fill=color)

class Terrain:
    def __init__(self, width, depth, grid_size):
        self.vertices = []
        self.faces = []
        self.generate_terrain(width, depth, grid_size)

    def generate_terrain(self, width, depth, grid_size):
        rows = width // grid_size
        cols = depth // grid_size
        for x in range(rows):
            for z in range(cols):
                y = random.randint(-10, 10)
                self.vertices.append((x * grid_size, y, z * grid_size))

        for x in range(rows - 1):
            for z in range(cols - 1):
                top_left = x * cols + z
                top_right = top_left + 1
                bottom_left = top_left + cols
                bottom_right = bottom_left + 1
                self.faces.append((top_left, bottom_left, bottom_right))
                self.faces.append((top_left, bottom_right, top_right))

    def update(self):
        pass

    def render(self, canvas, engine):
        for face in self.faces:
            points = [engine.project_3d_to_2d(*self.vertices[v]) for v in face]
            flat_points = [p for point in points for p in point]
            canvas.create_polygon(flat_points, outline="green", fill="", width=1)

if __name__ == "__main__":
    engine = GraphicsEngine(800, 600, "DragEngine 3D")

    terrain = Terrain(800, 800, 50)
    engine.add_object(terrain)

    try:
        engine.main_loop()
    except tk.TclError:
        engine.stop()
