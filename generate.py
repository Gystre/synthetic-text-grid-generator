from typing import Union
import numpy as np
import colorsys
from PIL import Image, ImageFont, ImageDraw
import argparse
import random
import time
import os
import time
from matplotlib import pyplot as plt

char_to_int_map = {
    "A": 0, "B": 1, "C": 2, "D": 3, "E": 4, "F": 5, "G": 6, "H": 7, "I": 8, "J": 9, "K": 10, "L": 11, "M": 12, "N": 13, "O": 14, "P": 15, "Q": 16, "R": 17, "S": 18, "T": 19, "U": 20, "V": 21, "W": 22, "X": 23, "Y": 24, "Z": 25,
    "0": 26, "1": 27, "2": 28, "3": 29, "4": 30, "5": 31, "6": 32, "7": 33, "8": 34, "9": 35,
}

# stats for graphs
chars = {
    "A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0, "I": 0, "J": 0, "K": 0, "L": 0, "M": 0, "N": 0, "O": 0, "P": 0, "Q": 0, "R": 0, "S": 0, "T": 0, "U": 0, "V": 0, "W": 0, "X": 0, "Y": 0, "Z": 0,
    "0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0, "8": 0, "9": 0,
}

sizes = {
    "sm": 0,
    "md": 0,
    "lg": 0
}

shapes = {
    "sq": 0,
    "lr": 0,
    "tr": 0
}

fonts = {}

widths = []
heights = []

# grid lines on image
DRAW_GRID_LINES_CHANCE = 0.20

# no circles at all
NO_COLORS_BG_CHANCE = 0.60

# if we are drawing circles, chance of circle behind character
DRAW_CIRCLE_CHANCE = 0.20

# no colored text
NO_COLORS_FONT_CHANCE = 0.20

# if we are changing font colors, chance of changing the character's font color
CHANGE_FONT_COLOR_CHANCE = 0.10


def convert(bbox, w, h):
    # pillow bb -> yolo v5 coords
    # xmin, ymin, xmax, ymax
    x_center = ((bbox[2] + bbox[0]) / 2) / w
    y_center = ((bbox[3] + bbox[1]) / 2) / h
    width = (bbox[2] - bbox[0]) / w
    height = (bbox[3] - bbox[1]) / h

    if x_center < 0 or y_center < 0:
        raise Exception("x or y < 0:", x_center, y_center)

    if width < 0 or height < 0:
        raise Exception("width or height < 0:", width, height)
    return [x_center, y_center, width, height]


def gen_bright_rgb() -> Union[int, int, int]:
    h, s, l = random.random(), 0.5 + random.random()/2.0, 0.4 + random.random()/5.0
    return [int(256*i) for i in colorsys.hls_to_rgb(h, l, s)]


def generate_image(dir: str, category: str):
    # randomize stuff
    # small, medium, large
    type = random.choice(["sm", "md", "lg"])
    sizes[type] += 1
    dim, font_size = 0, 0
    padding = random.randint(5, 10)
    if type == "sm":
        dim = random.randint(4, 15)
        font_size = random.randint(40, 60)
    elif type == "md":
        dim = random.randint(15, 30)
        font_size = random.randint(30, 40)
    elif type == "lg":
        dim = random.randint(30, 45)
        font_size = random.randint(20, 35)

    # determine the overall shape by modifying the ratio of the dimensions
    # square, long rectangle, tall rectange
    shape = random.choice(["sq", "lr", "tr"])
    shapes[shape] += 1
    dim_x, dim_y = 0, 0
    if shape == "sq":
        dim_x = dim
        dim_y = dim
    elif shape == "lr":
        dim_x = random.randint(dim, int(dim * 1.5))
        dim_y = dim
    elif shape == "tr":
        dim_x = dim
        dim_y = random.randint(dim, int(dim * 1.5))

    # numbers under represented rn
    set_of_chars = random.choice(["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz",
                                  "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "abcdefghijklmnopqrstuvwxyz0123456789", "0123456789"])

    font_file = random.choice(list(fonts.keys()))
    font = ImageFont.truetype(
        font="fonts/" + font_file + ".ttf", size=font_size)
    fonts[font_file] += 1
    (width, _), (_, _) = font.font.getsize("W")

    # wide font then use big padding
    if width > 50:
        padding = random.randint(13, 20)

    # actually start drawing the image
    x_outer_padding = random.randint(10, 30)
    y_outer_padding = random.randint(5, 10)
    img = Image.new("RGB", (
        dim_x * (font_size + padding * 2) + x_outer_padding,
        dim_y * (font_size + padding * 2) + y_outer_padding
    ), color="white")
    widths.append(img.width)
    heights.append(img.height)

    draw = ImageDraw.Draw(img)

    rand = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
                   for i in range(3))
    (font_name, _) = font.getname()
    name = f"{rand}-{type}_{shape}_{dim_x}x{dim_y}_f{font_size}px_p{padding}px_{font_name}"

    file = open(f"{dir}/labels/{category}/{name}.txt", "w")

    # draw grid lines
    if random.random() < DRAW_GRID_LINES_CHANCE:
        for x in range(dim_x):
            x_coord = x * (font_size + padding * 2) + x_outer_padding
            x_coord -= 6  # shift over a little bit
            draw.line([(x_coord, 0), (x_coord, img.height)], fill="black")

        for y in range(dim_y):
            y_coord = y * (font_size + padding * 2) + y_outer_padding
            y_coord -= 4
            draw.line([(0, y_coord), (img.width, y_coord)], fill="black")

    no_colors_bg = False
    if random.random() < NO_COLORS_BG_CHANCE:
        no_colors_bg = True

    no_colors_font = False
    if random.random() < NO_COLORS_FONT_CHANCE:
        no_colors_font = True

    # draw text
    for x in range(dim_x):
        for y in range(dim_y):
            text = random.choice(set_of_chars)
            x_coord = x * (font_size + padding * 2) + x_outer_padding
            y_coord = y * (font_size + padding * 2) + y_outer_padding
            y_coord -= font_size * 0.07  # try to keep really tall fonts inside image

            bb = draw.textbbox((x_coord, y_coord), text,
                               font=font)
            (bbx, bby, w, h) = convert(bb, img.width, img.height)

            char = text if text.isdigit() else text.upper()
            chars[char] += 1
            file.write(
                f"{char_to_int_map[char]} {bbx} {bby} {w} {h}\n")
            # draw.rectangle(bb, outline="green")
            drawing_circle = random.random() < DRAW_CIRCLE_CHANCE
            if drawing_circle and not no_colors_bg:
                # make a random bright color
                r, g, b = gen_bright_rgb()
                circle_size = random.randint(5, 8)
                draw.ellipse([(bb[0] - circle_size, bb[1] - circle_size),
                              (bb[2] + circle_size, bb[3] + circle_size)],
                             fill=(r, g, b))

            fill_color = "black"
            if random.random() < DRAW_CIRCLE_CHANCE and not no_colors_font and not drawing_circle:
                r, g, b = gen_bright_rgb()
                fill_color = (r, g, b)

            draw.text((x_coord, y_coord), text, font=font, fill=fill_color)

    img.save(f"{dir}/images/{category}/{name}.jpg")
    file.close()


if __name__ == "__main__":
    random.seed(time.time())

    argparse = argparse.ArgumentParser(description="ballin")
    argparse.add_argument('--amt', type=int, default=100,
                          help="amount of images to generate")
    args = argparse.parse_args()
    amt = args.amt

    # read font names for stats
    if not os.listdir("fonts/"):
        os.makedirs("fonts")
        print("Place some .ttf font files in the fonts/ folder, exiting...")
        exit(0)
    for file in os.listdir("fonts/"):
        file_name = file[:file.rfind(".")]
        fonts.update({file_name: 0})

    print("Creating", amt, "images...")

    # make dirs
    if not os.path.exists("generated"):
        os.makedirs("generated")

    name = str(int(time.time())) + "_" + time.strftime("%m-%d-%Y") + \
        "_" + str(amt) + "imgs"
    dir = "generated/" + name
    if not os.path.exists(dir):
        os.makedirs(dir)

    if not os.path.exists(dir + "/images"):
        os.makedirs(dir + "/images")

    if not os.path.exists(dir + "/labels"):
        os.makedirs(dir + "/labels")

    folders = ["images", "labels"]
    for i in folders:
        if not os.path.exists(f"{dir}/{i}/train"):
            os.makedirs(f"{dir}/{i}/train")

        if not os.path.exists(f"{dir}/{i}/val"):
            os.makedirs(f"{dir}/{i}/val")

        if not os.path.exists(f"{dir}/{i}/test"):
            os.makedirs(f"{dir}/{i}/test")

    # generate imgs
    start_time = time.time()
    train_amt = int(amt * 0.7)
    validate_amt = int(amt * 0.2)
    test_amt = int(amt * 0.1)
    for i in range(train_amt):
        generate_image(dir, "train")

    for i in range(validate_amt):
        generate_image(dir, "val")

    for i in range(test_amt):
        generate_image(dir, "test")

    print("Finished in:", str(int(time.time() - start_time)), "seconds")
    print("Generated:", amt, "images")
    print("Saved to:", dir)
    print("Train:", train_amt, "images")
    print("Validate:", validate_amt, "images")
    print("Test:", test_amt, "images")

    # write yaml
    file = open(f"{dir}/{name}.yaml", "w")
    file.write(f"path: ../datasets/{name}/images\n")
    file.write(f"train: train\n")
    file.write(f"val: val\n")
    file.write(f"test: test\n")
    file.write("\n")
    file.write("nc: " + str(len(char_to_int_map)) + "\n")
    file.write("\n")
    classes = "["
    for keys in char_to_int_map:
        classes += "'" + keys + "',"
    classes = classes[:-1]
    classes += "]"
    file.write(f"names: {classes}\n")
    file.close()

    # do graphs
    plt.figure(figsize=(17, 10))
    plt.subplot2grid((3, 2), (0, 0))
    plt.bar(list(sizes.keys()), list(sizes.values()), tick_label=["small", "medium", "large"],
            width=0.7, color=["blue", "green", "red"])
    plt.title("Size")
    plt.ylabel("Amount")

    plt.subplot2grid((3, 2), (0, 1))
    plt.bar(list(shapes.keys()), list(shapes.values()), tick_label=["square", "long rect", "tall rect"],
            width=0.7, color=["blue", "green", "red"])
    plt.title("Shape")
    plt.ylabel("Amount")

    plt.subplot2grid((3, 2), (1, 0))
    plt.bar(list(chars.keys()), list(chars.values()), tick_label=list(chars.keys()),
            width=0.7)
    plt.title("Characters")
    plt.ylabel("Amount")

    plt.subplot2grid((3, 2), (1, 1))
    plt.scatter(widths, heights, c=widths, cmap="viridis")
    plt.colorbar()
    plt.title("Resolutions")
    plt.xlabel("Width")
    plt.ylabel("Height")

    # make regression line for resolutions
    m, b = np.polyfit(widths, heights, 1)
    plt.plot(widths, m * np.array(widths) + b, color="red")

    # fonts graph
    plt.subplot2grid((3, 2), (2, 0), colspan=2)
    plt.bar(list(fonts.keys()), list(fonts.values()),
            tick_label=list(fonts.keys()))
    plt.title("Fonts")
    plt.ylabel("Amount")
    plt.xticks(rotation=45, ha="right")

    plt.savefig(f"{dir}/stats.jpg")
    plt.show()
