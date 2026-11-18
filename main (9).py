import colorsys
import math
import random
import shutil
import sys
import time

RESET = "\033[0m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
CURSOR_HOME = "\033[H"
CLEAR_SCREEN = "\033[2J\033[H"


def get_replit_size():
    """Safely gets terminal size on Replit Console or Shell."""
    try:
        size = shutil.get_terminal_size(fallback=(78, 28))
        w = size.columns - 1 if size.columns >= 40 else 78
        h = size.lines - 2 if size.lines >= 15 else 28
        return min(w, 120), min(h, 46)
    except Exception:
        return 78, 28


def hsv_to_rgb_255(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(
        h % 1.0, max(0.0, min(1.0, s)), max(0.0, min(1.0, v))
    )
    return int(r * 255), int(g * 255), int(b * 255)


def blend_rgb(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class SkyAndMeteors:
    """Manages twinkling stars and streaking neon shooting stars."""

    def __init__(self, width, horizon_y):
        self.width = width
        self.horizon_y = max(6, horizon_y)
        self.stars = [
            {
                "x": random.randint(0, width - 1),
                "y": random.randint(0, self.horizon_y - 2),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.08, 0.2),
                "hue": random.choice([0.52, 0.85, 0.14, 0.65]),
            }
            for _ in range(int(width * self.horizon_y * 0.04))
        ]
        self.meteors = []

    def update(self):
        if random.random() < 0.07 and len(self.meteors) < 3:
            self.meteors.append({
                "x": random.uniform(5, self.width - 15),
                "y": random.uniform(0, self.horizon_y * 0.35),
                "vx": random.uniform(1.1, 2.2),
                "vy": random.uniform(0.45, 0.85),
                "life": 1.0,
            })

        alive = []
        for m in self.meteors:
            m["x"] += m["vx"]
            m["y"] += m["vy"]
            m["life"] -= 0.065
            if m["life"] > 0 and m["y"] < self.horizon_y and m["x"] < self.width:
                alive.append(m)
        self.meteors = alive

    def draw(self, fb, t):
        for s in self.stars:
            twinkle = 0.4 + 0.6 * ((math.sin(s["phase"] + t * s["speed"] * 15.0) + 1.0) * 0.5)
            star_col = hsv_to_rgb_255(s["hue"], 0.35, twinkle)
            bg = fb[s["y"]][s["x"]]
            fb[s["y"]][s["x"]] = blend_rgb(bg, star_col, 0.85)

        for m in self.meteors:
            for tail in range(7):
                tx = int(m["x"] - m["vx"] * tail * 0.6)
                ty = int(m["y"] - m["vy"] * tail * 0.6)
                if 0 <= tx < self.width and 0 <= ty < self.horizon_y:
                    fade = max(0.0, (1.0 - tail / 7.0) * m["life"])
                    col = hsv_to_rgb_255(0.51, 0.35 * (tail / 7.0), fade)
                    fb[ty][tx] = blend_rgb(fb[ty][tx], col, fade)
class SynthwaveRenderer:
    """
    Renders a 3D Cyberpunk Outrun Synthwave scene using HD sub-pixel half-blocks.
    Includes a sliced neon sun, scrolling wireframe mountains, and a 3D laser grid.
    """

    def __init__(self, width, char_height):
        self.width = width
        self.char_height = char_height
        self.pixel_height = char_height * 2
        self.horizon_y = int(self.pixel_height * 0.52)
        self.time_tick = 0.0
        self.sky = SkyAndMeteors(width, self.horizon_y)

    def _mountain_height(self, world_x):
        """Deterministic multi-octave ridge noise for scrolling mountain peaks."""
        h1 = abs(math.sin(world_x * 0.14)) * 1.0
        h2 = abs(math.cos(world_x * 0.31 + 1.2)) * 0.55
        h3 = abs(math.sin(world_x * 0.73 - 0.5)) * 0.25
        # Flatten the center valley so the giant sun shines between the peaks
        return (h1 + h2 + h3) * 0.55

    def render_frame(self):
        w = self.width
        ph = self.pixel_height
        hy = self.horizon_y
        cx = w / 2.0

        self.sky.update()

        # 1. Sky Gradient (Deep midnight indigo at top -> electric magenta haze at horizon)
        fb = [[(0, 0, 0)] * w for _ in range(ph)]
        for py in range(hy):
            sky_t = py / max(1, hy - 1)
            hue = 0.74 + (sky_t ** 1.6) * 0.16
            sat = 0.88 - (sky_t ** 2) * 0.12
            val = 0.06 + (sky_t ** 2.2) * 0.52
            row_col = hsv_to_rgb_255(hue, sat, val)
            for px in range(w):
                fb[py][px] = row_col

        self.sky.draw(fb, self.time_tick)

        # 2. Giant Retro-Futuristic Striped Sun + Outer Corona Glow
        sun_r = min(w * 0.21, hy * 0.76)
        sun_cy = hy - sun_r * 0.18

        for py in range(hy):
            dy = py - sun_cy
            for px in range(w):
                dx = px - cx
                dist = math.sqrt(dx * dx + dy * dy)

                # Soft atmospheric sun halo
                if sun_r <= dist < sun_r * 1.65:
                    glow = (1.0 - (dist - sun_r) / (sun_r * 0.65)) ** 2.2
                    halo_col = hsv_to_rgb_255(0.92, 0.9, 0.65)
                    fb[py][px] = blend_rgb(fb[py][px], halo_col, glow * 0.55)

                # Sun disc with classic horizontal scanline cutouts
                elif dist < sun_r:
                    # Normalized vertical position inside sun (0 = top, 1 = bottom)
                    sun_v = (dy + sun_r) / (2.0 * sun_r)
                    # Scanline stripes get thicker toward the bottom of the sun
                    stripe_wave = math.sin((sun_v ** 1.8) * 34.0 - self.time_tick * 1.4)
                    cutout_threshold = -0.35 + sun_v * 0.85

                    if sun_v < 0.42 or stripe_wave > cutout_threshold:
                        # Top of sun = blazing gold-yellow; bottom = hot neon pink-orange
                        hue = 0.14 - (sun_v ** 1.2) * 0.15
                        sat = 0.85 + sun_v * 0.15
                        fb[py][px] = hsv_to_rgb_255(hue, sat, 1.0)

        # 3. Scrolling Cyberpunk Mountain Range along the Horizon
        scroll_x = self.time_tick * 1.8
        for px in range(w):
            norm_x = (px - cx) / (w * 0.5)  # -1.0 to +1.0
            valley_mask = min(1.0, (abs(norm_x) * 1.45) ** 1.5)
            m_h = self._mountain_height(norm_x * 9.0 + scroll_x) * (hy * 0.52) * valley_mask
            peak_y = int(hy - m_h)

            for py in range(max(0, peak_y), hy):
                depth_in_mtn = (py - peak_y) / max(1, hy - peak_y)
                # Glowing neon cyan/magenta rim on the top 2 pixels of the mountain ridge
                if py - peak_y <= 1 and m_h > 1.5:
                    rim_hue = 0.52 if abs(norm_x) > 0.45 else 0.86
                    fb[py][px] = hsv_to_rgb_255(rim_hue, 0.85, 0.98)
                else:
                    # Dark purple silhouette with subtle contour shading
                    val = 0.06 + (1.0 - depth_in_mtn) * 0.11
                    fb[py][px] = hsv_to_rgb_255(0.76, 0.9, val)

        # 4. 3D Perspective Neon Laser Grid Floor
        camera_speed = self.time_tick * 3.8
        sway = math.sin(self.time_tick * 0.5) * 1.6

        for py in range(hy, ph):
            # Screen Y distance below horizon (1 at horizon -> ph-hy at bottom)
            screen_dy = (py - hy) + 0.6
            # True 3D perspective depth Z = 1 / screen_dy
            z = (ph - hy) / screen_dy
            fog = max(0.0, min(1.0, 1.0 - (z / 18.0)))

            # Base floor color (deep synthwave violet)
            floor_col = hsv_to_rgb_255(0.76, 0.92, 0.05 + fog * 0.08)

            # Moving horizontal grid lines
            z_coord = z * 1.6 + camera_speed
            z_frac = abs((z_coord % 1.0) - 0.5)
            z_line = max(0.0, 1.0 - (z_frac / (0.045 + 0.025 * fog)))

            for px in range(w):
                # World X coordinate scales linearly with depth Z
                world_x = ((px - cx) / (w * 0.36)) * z + sway
                x_frac = abs((world_x % 1.0) - 0.5)
                x_line = max(0.0, 1.0 - (x_frac / 0.045))

                grid_intensity = max(z_line, x_line) ** 1.6

                # Sun reflection shimmer down the center of the floor
                sun_reflect = max(0.0, 1.0 - abs(px - cx) / (sun_r * 0.95))
                ripple = 0.65 + 0.35 * math.sin(z * 5.0 - self.time_tick * 4.0)
                reflect_strength = (sun_reflect ** 2.2) * ripple * fog * 0.42

                pixel_col = blend_rgb(floor_col, (255, 60, 150), reflect_strength)

                if grid_intensity > 0.02:
                    # Neon cyan near center, hot magenta toward outer edges
                    edge_mix = min(1.0, abs(px - cx) / (w * 0.48))
                    grid_hue = 0.51 + edge_mix * 0.36
                    neon_col = hsv_to_rgb_255(grid_hue, 0.85, min(1.0, fog * 1.25))
                    pixel_col = blend_rgb(pixel_col, neon_col, grid_intensity * fog)

                fb[py][px] = pixel_col

        # Horizon glowing laser seam
        for px in range(w):
            fb[hy][px] = hsv_to_rgb_255(0.86, 0.75, 0.95)

        self.time_tick += 0.07

        # 5. Pack pairs of vertical pixels into terminal rows using '▀'
        frame_lines = []
        for row in range(self.char_height):
            top_row = fb[row * 2]
            bot_row = fb[row * 2 + 1]
            line = []
            last_pair = None
            for col in range(w):
                tr, tg, tb = top_row[col]
                br, bg, bb = bot_row[col]
                pair = (tr, tg, tb, br, bg, bb)
                if pair != last_pair:
                    last_pair = pair
                    line.append(f"\033[38;2;{tr};{tg};{tb};48;2;{br};{bg};{bb}m")
                line.append("▀")
            frame_lines.append("".join(line) + RESET)

        return CURSOR_HOME + "\n".join(frame_lines)


def main():
    sys.stdout.write(CLEAR_SCREEN + HIDE_CURSOR)
    sys.stdout.flush()

    try:
        width, height = get_replit_size()
        scene = SynthwaveRenderer(width, height)

        while True:
            start_time = time.time()

            new_w, new_h = get_replit_size()
            if new_w != width or new_h != height:
                width, height = new_w, new_h
                scene = SynthwaveRenderer(width, height)
                sys.stdout.write(CLEAR_SCREEN)

            frame = scene.render_frame()
            sys.stdout.write(frame)
            sys.stdout.flush()

            elapsed = time.time() - start_time
            time.sleep(max(0.0, (1.0 / 24.0) - elapsed))

    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET + "\nSynthwave simulation terminated.\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
