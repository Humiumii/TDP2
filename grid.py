import math
import os

from audio import start_instance


def draw_grid(proj_pos, player_pos, obstacles):
    os.system("cls" if os.name == "nt" else "clear")
    size = 35

    for y in range(size):
        row = ""

        for x in range(size):
            current_pos = (y, x)

            if current_pos == proj_pos:
                row += " * "
            elif current_pos == player_pos:
                row += " @ "
            elif current_pos in obstacles:
                row += " X "
            else:
                row += " . "

        print(row)


def draw_sonar(current_radius, player_pos, obstacles, play_audio=True):
    os.system("cls" if os.name == "nt" else "clear")
    size = 35
    py, px = player_pos

    for y in range(size):
        row = ""

        for x in range(size):
            dist = math.sqrt((y - py) ** 2 + (x - px) ** 2)

            if (y, x) == player_pos:
                row += " @ "
            elif (y, x) in obstacles and abs(dist - current_radius) < 0.5:
                row += " X "
                if play_audio:
                    try:
                        start_instance("ping.mp3")
                    except Exception:
                        pass
            elif abs(dist - current_radius) < 0.5:
                row += " ) "
            else:
                row += " . "

        print(row)
