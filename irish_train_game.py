import math
import time
import tkinter as tk
from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    name: str
    county: str
    km: float


class EmeraldLineGame:
    """A small, asset-free train driving game for the Belfast-Dublin route."""

    COLORS = {
        "navy": "#071d2b",
        "navy_light": "#0c2d3e",
        "cream": "#f7f0df",
        "muted": "#a6bdc0",
        "green": "#16805c",
        "green_dark": "#0b5a43",
        "orange": "#f29d49",
        "yellow": "#f3ca5d",
        "red": "#df6b57",
        "sky": "#b7dce1",
        "field": "#89b96b",
        "field_dark": "#5b985e",
        "track": "#3c4650",
        "rail": "#d9d6c9",
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Emerald Line: An Irish Train Game")
        self.root.configure(bg=self.COLORS["navy"])
        self.root.minsize(900, 600)
        self.root.geometry("1120x700")

        self.canvas = tk.Canvas(
            root,
            background=self.COLORS["navy"],
            highlightthickness=0,
            cursor="arrow",
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _event: self.draw())
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind_all("<KeyPress>", self.on_key_down)
        self.root.bind_all("<KeyRelease>", self.on_key_up)
        self.canvas.focus_set()

        self.stations = (
            Station("Belfast Grand Central", "Belfast", 0),
            Station("Portadown", "Armagh", 28),
            Station("Newry", "Down", 53),
            Station("Dundalk", "Louth", 79),
            Station("Drogheda", "Louth", 112),
            Station("Dublin Connolly", "Dublin", 150),
        )
        self.keys = set()
        self.last_time = time.perf_counter()
        self.reset(started=False)
        self.root.after(50, self.tick)

    def reset(self, started=False):
        self.started = started
        self.finished = False
        self.completed = False
        self.paused = False
        self.position = 0.0
        self.speed = 0.0
        self.throttle = 0.0
        self.brake = 0.0
        self.next_station_index = 1
        self.last_stop_name = "Belfast Grand Central"
        self.score = 0
        self.stops = 0
        self.missed = 0
        self.message = (
            "Welcome aboard. Take the Emerald Line south from Belfast to Dublin."
        )
        self.dwell = 0.0
        self.overspeed = False
        self.last_time = time.perf_counter()

    def begin(self):
        self.started = True
        self.paused = False
        self.last_time = time.perf_counter()
        self.message = "Service ready. Hold UP or W to build speed."

    def on_click(self, _event):
        if not self.started or self.finished:
            self.reset(started=True)
            self.message = "Service ready. Hold UP or W to build speed."
        self.canvas.focus_set()

    def on_key_down(self, event):
        key = event.keysym.lower()
        if key in {"up", "down", "left", "right", "w", "a", "s", "d", "space"}:
            self.keys.add(key)

        if key in {"return", "kp_enter"}:
            if not self.started or self.finished:
                self.reset(started=True)
                self.message = "Service ready. Hold UP or W to build speed."
        elif key == "r":
            self.reset(started=True)
            self.message = "New service ready. Mind the speed boards this time."
        elif key == "p" and self.started and not self.finished:
            self.paused = not self.paused
            self.message = "Paused. Press P to continue." if self.paused else "Back on the line."

    def on_key_up(self, event):
        self.keys.discard(event.keysym.lower())

    def key_held(self, *keys):
        return any(key in self.keys for key in keys)

    def current_station(self):
        if self.next_station_index >= len(self.stations):
            return None
        return self.stations[self.next_station_index]

    def speed_limit(self):
        station = self.current_station()
        if station is None:
            return 110
        distance = station.km - self.position
        if distance < 7:
            return 35
        if distance < 16:
            return 65
        return 110

    def update(self, dt):
        if self.finished:
            return

        if self.dwell > 0:
            self.speed = 0
            self.throttle = 0
            self.dwell = max(0, self.dwell - dt)
            return

        if self.last_stop_name and self.next_station_index > 1 and self.key_held("up", "w"):
            self.last_stop_name = ""

        if self.key_held("up", "w"):
            self.throttle = min(100, self.throttle + 62 * dt)
        else:
            self.throttle = max(0, self.throttle - 82 * dt)

        if self.key_held("down", "s", "space"):
            self.brake = min(1, self.brake + 4.5 * dt)
        else:
            self.brake = max(0, self.brake - 2.2 * dt)

        acceleration = (self.throttle / 100) * 23
        acceleration -= self.brake * 42
        if self.speed > 0:
            acceleration -= 1.3
        self.speed = max(0, min(120, self.speed + acceleration * dt))

        previous_limit = self.speed_limit()
        self.position += self.speed * dt / 36
        self.overspeed = self.speed > previous_limit + 8
        self.check_station()

    def check_station(self):
        station = self.current_station()
        if station is None:
            return

        distance = station.km - self.position
        if abs(distance) <= 1.5 and self.speed <= 14:
            self.position = station.km
            self.speed = 0
            self.throttle = 0
            self.brake = 1
            self.stops += 1
            self.next_station_index += 1
            points = 300 + max(0, int(150 - abs(distance) * 100))
            self.score += points
            self.last_stop_name = station.name

            if self.next_station_index >= len(self.stations):
                self.finished = True
                self.completed = True
                self.message = (
                    f"Dublin Connolly arrival secured. Excellent driving, driver. +{points}"
                )
            else:
                self.dwell = 2.0
                next_station = self.current_station()
                self.message = (
                    f"Platform stop at {station.name} secured. +{points}  "
                    f"Next: {next_station.name}."
                )
            return

        if distance < -2.5:
            self.missed += 1
            self.score = max(0, self.score - 150)
            missed_name = station.name
            self.next_station_index += 1
            self.message = f"You passed {missed_name}. The signal box noted that one."
            if self.next_station_index >= len(self.stations):
                self.finished = True
                self.completed = False
                self.message = "Dublin Connolly was passed. Service ended without a platform stop."

    def tick(self):
        now = time.perf_counter()
        dt = min(0.12, now - self.last_time)
        self.last_time = now

        if self.started and not self.paused:
            self.update(dt)
        self.draw()
        self.root.after(50, self.tick)

    def draw(self):
        canvas = self.canvas
        width = max(canvas.winfo_width(), 900)
        height = max(canvas.winfo_height(), 600)
        canvas.delete("all")

        header_bottom = 82
        footer_top = height - 122
        scene_bottom = footer_top
        track_y = scene_bottom - 94
        train_x = max(205, width * 0.255)
        scale = max(5.2, min(8.5, width / 132))

        self.draw_header(width, header_bottom)
        self.draw_landscape(width, header_bottom, scene_bottom, track_y, train_x, scale)
        self.draw_route(width, track_y, train_x, scale)
        self.draw_train(train_x, track_y)
        self.draw_footer(width, height, footer_top)

        if not self.started:
            self.draw_start_overlay(width, header_bottom, scene_bottom)
        elif self.paused:
            self.draw_pause_overlay(width, header_bottom, scene_bottom)
        elif self.finished:
            self.draw_finish_overlay(width, header_bottom, scene_bottom)

    def draw_header(self, width, header_bottom):
        c = self.canvas
        navy = self.COLORS["navy"]
        light = self.COLORS["cream"]
        muted = self.COLORS["muted"]
        c.create_rectangle(0, 0, width, header_bottom, fill=navy, outline=navy)
        c.create_rectangle(0, header_bottom - 3, width, header_bottom, fill=self.COLORS["orange"], outline="")
        c.create_text(
            32,
            23,
            text="EMERALD LINE",
            anchor="w",
            fill=light,
            font=("Segoe UI", 21, "bold"),
        )
        c.create_text(
            34,
            54,
            text="BELFAST GRAND CENTRAL  /  PORTADOWN  /  NEWRY  /  DUNDALK  /  DROGHEDA  /  DUBLIN CONNOLLY",
            anchor="w",
            fill=muted,
            font=("Segoe UI", 9, "bold"),
        )

        progress = min(1, self.position / self.stations[-1].km)
        bar_left = width - 305
        bar_right = width - 118
        c.create_text(
            bar_left,
            25,
            text=f"SCORE  {self.score:04d}",
            anchor="w",
            fill=light,
            font=("Segoe UI", 12, "bold"),
        )
        c.create_text(
            bar_left,
            51,
            text=f"ROUTE  {int(progress * 100):02d}%",
            anchor="w",
            fill=muted,
            font=("Segoe UI", 9, "bold"),
        )
        c.create_rectangle(bar_right, 45, width - 32, 52, fill="#234454", outline="")
        c.create_rectangle(
            bar_right,
            45,
            bar_right + (width - 32 - bar_right) * progress,
            52,
            fill=self.COLORS["green"],
            outline="",
        )

    def draw_landscape(self, width, top, bottom, track_y, train_x, scale):
        c = self.canvas
        colors = self.COLORS
        horizon = top + (bottom - top) * 0.42
        c.create_rectangle(0, top, width, horizon, fill=colors["sky"], outline="")
        c.create_rectangle(0, horizon, width, bottom, fill=colors["field"], outline="")

        c.create_oval(width - 142, top + 28, width - 84, top + 86, fill="#f6c76d", outline="")
        c.create_text(
            width - 113,
            top + 105,
            text="WEST",
            fill="#678c88",
            font=("Segoe UI", 8, "bold"),
        )

        cloud_shift = -(self.position * scale * 0.12) % 300
        for base_x in range(-300, width + 301, 300):
            x = base_x + cloud_shift
            c.create_oval(x, top + 62, x + 74, top + 83, fill="#dceced", outline="")
            c.create_oval(x + 27, top + 48, x + 113, top + 83, fill="#dceced", outline="")
            c.create_oval(x + 79, top + 64, x + 136, top + 83, fill="#dceced", outline="")

        far_shift = -(self.position * scale * 0.22) % 520
        for base_x in range(-520, width + 521, 520):
            x = base_x + far_shift
            c.create_polygon(
                x,
                horizon + 34,
                x + 155,
                horizon - 72,
                x + 300,
                horizon + 26,
                x + 418,
                horizon - 44,
                x + 570,
                horizon + 32,
                fill="#7da6a0",
                outline="",
            )

        c.create_rectangle(0, horizon + 42, width, horizon + 47, fill="#6d9a66", outline="")
        c.create_rectangle(0, horizon + 48, width, horizon + 53, fill="#477c58", outline="")

        field_shift = -(self.position * scale * 0.6) % 190
        for base_x in range(-190, width + 191, 190):
            x = base_x + field_shift
            c.create_polygon(
                x,
                horizon + 54,
                x + 95,
                horizon + 54,
                x + 70,
                track_y - 24,
                x - 24,
                track_y - 24,
                fill="#9cc875",
                outline="",
            )
            for stripe in range(4):
                stripe_x = x + 12 + stripe * 17
                c.create_line(
                    stripe_x,
                    horizon + 67,
                    stripe_x - 29,
                    track_y - 28,
                    fill="#76aa68",
                    width=1,
                )

        # The hedgerows and trees are tied to route kilometres, so the world moves
        # while the train stays in view.
        for km in range(-45, 201, 5):
            x = train_x + (km - self.position) * scale
            if -70 <= x <= width + 70:
                tree_height = 30 + int(abs(math.sin(km * 1.37)) * 25)
                self.draw_tree(x, track_y - 35, tree_height)

        c.create_rectangle(0, track_y - 27, width, track_y - 18, fill="#4f8759", outline="")
        c.create_line(0, track_y - 23, width, track_y - 23, fill="#2f704f", width=2)

    def draw_tree(self, x, base_y, tree_height):
        c = self.canvas
        trunk = "#735a43"
        leaf = "#347451"
        leaf_light = "#4e9160"
        c.create_rectangle(x - 3, base_y - tree_height * 0.43, x + 3, base_y + 2, fill=trunk, outline="")
        c.create_oval(
            x - 18,
            base_y - tree_height,
            x + 14,
            base_y - tree_height * 0.35,
            fill=leaf,
            outline="",
        )
        c.create_oval(
            x - 7,
            base_y - tree_height * 1.12,
            x + 23,
            base_y - tree_height * 0.48,
            fill=leaf_light,
            outline="",
        )

    def draw_route(self, width, track_y, train_x, scale):
        c = self.canvas
        colors = self.COLORS
        c.create_polygon(
            0,
            track_y - 8,
            width,
            track_y - 8,
            width,
            track_y + 35,
            0,
            track_y + 35,
            fill=colors["track"],
            outline="",
        )

        tie_shift = -(self.position * scale) % 29
        for x in range(-40, width + 41, 29):
            tie_x = x + tie_shift
            c.create_rectangle(tie_x, track_y + 1, tie_x + 7, track_y + 29, fill="#795e4b", outline="")
        c.create_line(0, track_y + 2, width, track_y + 2, fill=colors["rail"], width=3)
        c.create_line(0, track_y + 23, width, track_y + 23, fill=colors["rail"], width=3)

        station = self.current_station()
        for index, item in enumerate(self.stations):
            x = train_x + (item.km - self.position) * scale
            if -100 <= x <= width + 100:
                self.draw_station(item, x, track_y, index == self.next_station_index)

        if station is not None:
            signal_x = train_x + (station.km - 8 - self.position) * scale
            if -30 <= signal_x <= width + 30:
                signal_color = colors["red"] if self.speed > self.speed_limit() + 8 else colors["green"]
                c.create_line(signal_x, track_y - 61, signal_x, track_y - 5, fill="#536168", width=3)
                c.create_rectangle(signal_x - 9, track_y - 75, signal_x + 9, track_y - 52, fill="#273842", outline="")
                c.create_oval(signal_x - 5, track_y - 71, signal_x + 5, track_y - 61, fill=signal_color, outline="")

    def draw_station(self, station, x, track_y, is_next):
        c = self.canvas
        if is_next:
            board = self.COLORS["orange"]
            board_text = self.COLORS["navy"]
            c.create_polygon(
                x,
                track_y - 116,
                x - 7,
                track_y - 103,
                x + 7,
                track_y - 103,
                fill=self.COLORS["orange"],
                outline="",
            )
        else:
            board = self.COLORS["navy_light"]
            board_text = self.COLORS["cream"]

        c.create_rectangle(x - 2, track_y - 68, x + 2, track_y + 3, fill="#5c665e", outline="")
        c.create_rectangle(x - 53, track_y - 91, x + 53, track_y - 66, fill=board, outline="")
        c.create_text(
            x,
            track_y - 78,
            text=station.name.upper(),
            fill=board_text,
            font=("Segoe UI", 8, "bold"),
        )
        c.create_line(x - 37, track_y - 1, x + 37, track_y - 1, fill="#c8bd9d", width=5)
        c.create_line(x - 33, track_y + 8, x + 33, track_y + 8, fill="#a89e86", width=2)

    def draw_train(self, x, track_y):
        c = self.canvas
        body_top = track_y - 70
        body_bottom = track_y + 1
        c.create_oval(x - 25, track_y + 20, x + 208, track_y + 38, fill="#2b363a", outline="")

        for offset in (0, 72, 144):
            carriage_left = x + offset
            carriage_right = carriage_left + 78
            c.create_rectangle(
                carriage_left,
                body_top,
                carriage_right,
                body_bottom,
                fill=self.COLORS["green_dark"],
                outline="#063b30",
                width=2,
            )
            c.create_rectangle(
                carriage_left,
                body_top + 31,
                carriage_right,
                body_top + 43,
                fill=self.COLORS["cream"],
                outline="",
            )
            for window in range(3):
                window_left = carriage_left + 9 + window * 21
                c.create_rectangle(
                    window_left,
                    body_top + 10,
                    window_left + 14,
                    body_top + 27,
                    fill="#9cc7c6",
                    outline="#d6ebe3",
                )
            c.create_oval(carriage_left + 12, track_y - 7, carriage_left + 27, track_y + 8, fill="#1f272b", outline="")
            c.create_oval(carriage_left + 54, track_y - 7, carriage_left + 69, track_y + 8, fill="#1f272b", outline="")

        c.create_polygon(
            x - 24,
            body_bottom,
            x - 24,
            body_top + 18,
            x - 8,
            body_top,
            x + 2,
            body_top,
            x + 2,
            body_bottom,
            fill=self.COLORS["green"],
            outline="#063b30",
            width=2,
        )
        c.create_rectangle(x - 11, body_top + 10, x - 1, body_top + 28, fill="#9cc7c6", outline="#d6ebe3")
        c.create_rectangle(x - 25, body_top + 42, x - 20, body_top + 48, fill=self.COLORS["orange"], outline="")
        c.create_rectangle(x - 26, body_top + 51, x - 20, body_top + 57, fill=self.COLORS["yellow"], outline="")
        c.create_text(
            x + 35,
            body_top + 37,
            text="EMERALD",
            fill=self.COLORS["green_dark"],
            font=("Segoe UI", 6, "bold"),
        )

    def draw_footer(self, width, height, footer_top):
        c = self.canvas
        colors = self.COLORS
        c.create_rectangle(0, footer_top, width, height, fill=colors["navy"], outline="")

        next_station = self.current_station()
        if self.finished:
            target_text = "SERVICE COMPLETE"
            distance_text = ""
        elif next_station is None:
            target_text = "DUBLIN CONNOLLY"
            distance_text = ""
        else:
            distance = max(0, next_station.km - self.position)
            target_text = f"NEXT STOP  {next_station.name.upper()}"
            distance_text = f"{distance:05.1f} km  /  {next_station.county.upper()}"

        c.create_text(31, footer_top + 22, text=target_text, anchor="w", fill=colors["cream"], font=("Segoe UI", 11, "bold"))
        c.create_text(31, footer_top + 47, text=distance_text, anchor="w", fill=colors["muted"], font=("Segoe UI", 9, "bold"))

        speed_limit = self.speed_limit()
        speed_color = colors["red"] if self.overspeed else colors["yellow"]
        c.create_text(width - 246, footer_top + 22, text=f"{round(self.speed):03d} km/h", anchor="w", fill=colors["cream"], font=("Segoe UI", 17, "bold"))
        c.create_text(width - 246, footer_top + 48, text=f"LIMIT  {speed_limit:03d}", anchor="w", fill=speed_color, font=("Segoe UI", 9, "bold"))

        bar_left = width - 104
        bar_top = footer_top + 17
        c.create_text(bar_left, bar_top - 3, text="POWER", anchor="w", fill=colors["muted"], font=("Segoe UI", 8, "bold"))
        c.create_rectangle(bar_left, bar_top + 11, width - 30, bar_top + 20, fill="#234454", outline="")
        c.create_rectangle(bar_left, bar_top + 11, bar_left + (width - 30 - bar_left) * self.throttle / 100, bar_top + 20, fill=colors["green"], outline="")
        c.create_text(bar_left, bar_top + 36, text="BRAKE", anchor="w", fill=colors["muted"], font=("Segoe UI", 8, "bold"))
        c.create_rectangle(bar_left, bar_top + 50, width - 30, bar_top + 59, fill="#234454", outline="")
        c.create_rectangle(bar_left, bar_top + 50, bar_left + (width - 30 - bar_left) * self.brake, bar_top + 59, fill=colors["red"], outline="")

        c.create_text(
            31,
            height - 21,
            text="UP / W accelerate    DOWN / S brake    SPACE emergency brake    P pause    R restart",
            anchor="w",
            fill="#76969b",
            font=("Segoe UI", 9),
        )
        c.create_text(
            width - 30,
            height - 21,
            text=f"STOPS {self.stops}   MISSED {self.missed}",
            anchor="e",
            fill="#76969b",
            font=("Segoe UI", 9, "bold"),
        )

    def overlay_panel(self, width, top, bottom, panel_height):
        c = self.canvas
        left = width * 0.18
        right = width * 0.82
        center = width / 2
        panel_top = top + (bottom - top - panel_height) / 2
        panel_bottom = panel_top + panel_height
        c.create_rectangle(0, top, width, bottom, fill="#071d2b", stipple="gray50", outline="")
        c.create_rectangle(left, panel_top, right, panel_bottom, fill=self.COLORS["navy"], outline="#386172", width=2)
        c.create_rectangle(left, panel_top, right, panel_top + 6, fill=self.COLORS["orange"], outline="")
        return center, panel_top, panel_bottom

    def draw_start_overlay(self, width, top, bottom):
        c = self.canvas
        center, panel_top, _panel_bottom = self.overlay_panel(width, top, bottom, 286)
        c.create_text(center, panel_top + 51, text="THE EMERALD LINE", fill=self.COLORS["cream"], font=("Segoe UI", 26, "bold"))
        c.create_text(center, panel_top + 88, text="A short run across the heart of Ireland", fill=self.COLORS["orange"], font=("Segoe UI", 12, "bold"))
        c.create_text(
            center,
            panel_top + 132,
            text="Drive south from Belfast Grand Central and stop cleanly at every platform.\nSlow down for the speed boards near each station.",
            justify="center",
            fill=self.COLORS["muted"],
            font=("Segoe UI", 11),
        )
        c.create_rectangle(center - 154, panel_top + 191, center + 154, panel_top + 237, fill=self.COLORS["green"], outline="")
        c.create_text(center, panel_top + 214, text="PRESS ENTER OR CLICK TO DRIVE", fill=self.COLORS["cream"], font=("Segoe UI", 11, "bold"))

    def draw_pause_overlay(self, width, top, bottom):
        c = self.canvas
        center, panel_top, _panel_bottom = self.overlay_panel(width, top, bottom, 190)
        c.create_text(center, panel_top + 60, text="PAUSED", fill=self.COLORS["cream"], font=("Segoe UI", 26, "bold"))
        c.create_text(center, panel_top + 105, text="Press P to return to the cab", fill=self.COLORS["muted"], font=("Segoe UI", 12))
        c.create_text(center, panel_top + 144, text=self.message, fill=self.COLORS["orange"], font=("Segoe UI", 10, "bold"))

    def draw_finish_overlay(self, width, top, bottom):
        c = self.canvas
        center, panel_top, _panel_bottom = self.overlay_panel(width, top, bottom, 250)
        title = "JOURNEY COMPLETE" if self.completed else "SERVICE ENDED"
        subtitle = "Dublin Connolly is on the board." if self.completed else "The final platform stop was missed."
        c.create_text(center, panel_top + 53, text=title, fill=self.COLORS["cream"], font=("Segoe UI", 25, "bold"))
        c.create_text(center, panel_top + 88, text=subtitle, fill=self.COLORS["orange"], font=("Segoe UI", 12, "bold"))
        c.create_text(
            center,
            panel_top + 137,
            text=f"SCORE  {self.score:04d}       STOPS  {self.stops}       MISSED  {self.missed}",
            fill=self.COLORS["cream"],
            font=("Segoe UI", 12, "bold"),
        )
        c.create_rectangle(center - 142, panel_top + 177, center + 142, panel_top + 221, fill=self.COLORS["green"], outline="")
        c.create_text(center, panel_top + 199, text="PRESS R OR ENTER TO RUN AGAIN", fill=self.COLORS["cream"], font=("Segoe UI", 10, "bold"))


def main():
    root = tk.Tk()
    EmeraldLineGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
