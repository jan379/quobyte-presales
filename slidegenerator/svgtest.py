#!/usr/bin/env python3
import drawsvg as draw
import json

company_color_primary="#262262"
company_color_secondary="#1A4B7E"
company_color_tertiary="#39B54A"
company_color_text="white"
company_color_accent1="#5B84EC"
company_color_accent2="#343534"
company_color_accent3="#E6E6E6"

viewbox_width = 800
viewbox_height = 600
d = draw.Drawing(viewbox_width, viewbox_height, origin=(0,0), font_family='Nunito Sans')

# Draw text
d.append(draw.Text('Quobyte Rulez', 24, viewbox_width / 3, viewbox_height / 6, fill=company_color_text))  # 8pt text at (-10, -35)

def draw_server(x, y, size, title):
    # rounded corners, that is why we use rx/ry
    server_length = size
    server_height = size / 4
    server_center = [ server_length / 2, server_height / 2 ]
    padding = 4
    server = draw.Group(id='metadata', fill='none', stroke='none')
    # outline
    server.append(draw.Rectangle(x, y, server_length, server_height, rx='10', ry='10', fill=company_color_primary))
    server.append(draw.Text(title, 12, x - padding, y - padding, fill=company_color_text))
    d.append(server)
    print("Print a server")

server_start_x = 100
server_start_y = 200
for x in range (0, 3):
    server_start_x_previous = server_start_x
    server_start_y_previous = server_start_y
    server_start_x = server_start_x + 120
    draw_server(x=server_start_x, y=server_start_y, size=100, title="MyNode" + str(x))
    ##### Draw a line
    arrow_start = [ server_start_x_previous , server_start_y_previous ] 
    arrow_end = [ server_start_x , server_start_y ]
    d.append(draw.Line(*arrow_start, *arrow_end, 
        stroke=company_color_primary, 
        stroke_width=4, 
        fill='none',
        ))

# Draw an arbitrary path (a triangle in this case)
###p = draw.Path(stroke_width=6, stroke=company_color_secondary, fill=company_color_text, fill_opacity=0.2)
###p.M(0, 0)  # Start point
###p.C(-40, -30, -40, 30, 40, 00)  # Draw a curve to (70, -20)
###d.append(p)
###
d.set_pixel_scale(3)  # Set number of pixels per geometry unit
#d.set_render_size(400, 200)  # Alternative to set_pixel_scale
d.save_svg('example.svg')

