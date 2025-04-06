import drawsvg as draw
import svgutils.compose as sc

RINK = ((-100, 100), (-42.5, 42.5))
GOAL_OFFSET = 11
PADDING = 5

MAX_RINK_DIST = pow(pow(RINK[0][1] - RINK[0][0], 2) + pow(RINK[1][1], 2), 0.5)

def draw_rink_components():
    clip = draw.ClipPath()
    border = draw.Group(opacity=1.0)

    # rink border
    str_lines = [
        [-100+29, -42.5, 100-29, -42.5, 'black' ],
        [-100, -42.5+29, -100, 42.5-29, 'black' ],
        [100, -42.5+29, 100, 42.5-29, 'black' ],
        [-100+29, 42.5, 100-29, 42.5, 'black' ],
    ]
    items = [clip, border]
    for l in str_lines:
        for c in items:
            c.append(draw.Line(l[0], l[1], l[2], l[3],
                        stroke_width=1,
                        stroke=l[4]))
    # rink border
    arc_lines = [
        [-100+29, -42.5+29, 29, 90, 180],
        [-100+29, 42.5-29, 29, 180, 270],
        [100-29, 42.5-29, 29, 270, 0],
        [100-29, -42.5+29, 29, 0, 90],
    ]
    for l in arc_lines:
        for c in items:
            c.append(draw.ArcLine(l[0], l[1], l[2], l[3], l[4],
                        fill='none',
                        stroke_width=1,
                        stroke='black'))
    clip.append(draw.Rectangle( -100+29, -42.5, 200-29*2, 85, fill='none'))

    # red and blue lines
    inn_lines = [
        [-100+11, -42.5, -100+11, 42.5, 'red', 1 ],
        [100-11, -42.5, 100-11, 42.5, 'red', 1 ],
        [-100+11+60, -42.5, -100+11+60, 42.5, 'blue', 2 ],
        [100-11-60, -42.5, 100-11-60, 42.5, 'blue', 2 ],
    ]
    g = draw.Group(opacity=0.5, clip_path=clip)
    for l in inn_lines:
        g.append(draw.Line(l[0], l[1], l[2], l[3],
                    fill='none',
                    stroke_width=l[5],
                    stroke=l[4]))
    innarc_lines = [
        # creases
        [-100+11, 0, 8, 270, 90, 'red'],
        [100-11, 0, 8, 90, 270, 'red'],
        # circles
        [-100+31, 22, 15, 0, 360, 'red'],
        [100-31, 22, 15, 0, 360, 'red'],
        [-100+31, -22, 15, 0, 360, 'red'],
        [100-31, -22, 15, 0, 360, 'red'],
        # faceoff dots in circles
        [-100+31, 22, 1, 0, 360, 'red'],
        [100-31, 22, 1, 0, 360, 'red'],
        [-100+31, -22, 1, 0, 360, 'red'],
        [100-31, -22, 1, 0, 360, 'red'],
        # faceoff dots in neutral zone
        [-100+76, 22, 1, 0, 360, 'red'],
        [100-76, 22, 1, 0, 360, 'red'],
        [-100+76, -22, 1, 0, 360, 'red'],
        [100-76, -22, 1, 0, 360, 'red'],
    ]
    for l in innarc_lines:
        g.append(draw.ArcLine(l[0], l[1], l[2], l[3], l[4],
                    fill=l[5] if l[2] < 3 else 'none',
                    stroke_width=1,
                    stroke=l[5]))

    border.append(draw.Line(0, -42.5, 0, 42.5,
                fill='none',
                opacity=0.2,
                stroke_width=2,
                stroke='black'))

    return border, g

def draw_rink(filepath: str | None):
    border, g = draw_rink_components()
    d = draw.Drawing(
        RINK[0][1] - RINK[0][0] + PADDING, 
        RINK[1][1] - RINK[1][0] + PADDING, 
        origin='center')

    d.append(g)
    d.append(border)
    d.set_pixel_scale(2)  # Set number of pixels per geometry unit
    if filepath:
        d.save_svg(filepath)
    return d

def draw_half_rink(filepath: str | None):
    border, g = draw_rink_components()
    vert_offset = (RINK[0][1] - RINK[0][0] + PADDING) /2
    dhalf = draw.Drawing(
        RINK[1][1] - RINK[1][0] + PADDING, 
        (RINK[0][1] - RINK[0][0] + PADDING) /2, 
        origin='center')

    dhalf.append(draw.Use(border, vert_offset/2, 0, transform='rotate(90) scale(1)'))
    dhalf.append(draw.Use(g, vert_offset/2, 0, transform='rotate(90) scale(1)'))
    dhalf.set_pixel_scale(2)  # Set number of pixels per geometry unit
    if filepath:
        dhalf.save_svg(filepath)
    return dhalf