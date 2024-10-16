import drawsvg as draw

company_color_primary="#262262"
company_color_secondary="#1A4B7E"
company_color_tertiary="#39B54A"
company_color_text="white"
company_color_accent1="#5B84EC"
company_color_accent2="#343534"
company_color_accent3="#E6E6E6"

box_width=50
box_height=60

d = draw.Drawing(800, 600, origin='center', font_family='Nunito Sans', dominant_baseline='hanging')

# Draw text
d.append(draw.Text('Quobyte rulez', 24, -380, -280, fill=company_color_accent1))  # 8pt text at (-10, -35)


# Draw a rectangle2
r = draw.Rectangle(-395, -195, box_width, box_height, rx='10', ry='10', fill=company_color_primary)
r.append_title("Another Quobyte data service!")  # Add a tooltip
d.append(r)
d.append(draw.Text([' ', 'Metadata', 'Service'], 8, path=r, text_anchor='start', center=True, fill=company_color_text))

# Draw a rectangle2
r = draw.Rectangle(-245, -195, box_width, box_height, rx='10', ry='10', fill=company_color_secondary)
r.append_title("Another Quobyte data service!")  # Add1 a tooltip
d.append(r)
d.append(draw.Text([' ', 'Data', 'Service'], 8, path=r, text_anchor='start', center=True, fill=company_color_text))

# Draw an arbitrary path (a triangle in this case)
p = draw.Path(stroke_width=6, stroke=company_color_secondary, fill=company_color_text, fill_opacity=0.2)
p.M(0, 0)  # Start path at point (-55, -10)
p.C(-40, -30, -40, 30, 40, 00)  # Draw a curve to (70, -20)
d.append(p)

# Draw arrows
arrow = draw.Marker(-0.1, -0.51, 0.9, 0.5, scale=4, orient='auto')
arrow.append(draw.Lines(-0.1, 0.5, -0.1, -0.5, 0.9, 0, fill=company_color_tertiary, close=True))
p = draw.Path(stroke='red', stroke_width=2, fill='none',
        marker_end=arrow)  # Add an arrow to the end of a path
p.M(20, 40).L(20, 27).L(0, 20)  # Chain multiple path commands
d.append(p)
d.append(draw.Line(30, 20, 0, 10,
        stroke='red', stroke_width=2, fill='none',
        marker_end=arrow))  # Add an arrow to the end of a line

d.set_pixel_scale(2)  # Set number of pixels per geometry unit
#d.set_render_size(400, 200)  # Alternative to set_pixel_scale
d.save_svg('example.svg')

