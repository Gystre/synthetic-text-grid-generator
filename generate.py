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


def convert(size, box):
    # pillow bb -> yolo v5 coords
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x, y, w, h)


def generate_image(dir: str, category: str):
    # randomize stuff
    # small, medium, large
    type = random.choice(["sm", "md", "lg"])
    sizes[type] += 1
    dim, font_size = 0, 0
    padding = random.randint(3, 8)
    if type == "sm":
        dim = random.randint(4, 15)
        font_size = random.randint(40, 60)
    elif type == "md":
        dim = random.randint(15, 30)
        font_size = random.randint(20, 40)
    elif type == "lg":
        dim = random.randint(30, 50)
        font_size = random.randint(15, 20)

    # determine the overall shape by modifying the ratio of the dimensions
    # square, long rectangle, tall rectange
    shape = random.choice(["sq", "lr", "tr"])
    shapes[shape] += 1
    dim_x, dim_y = 0, 0
    if shape == "sq":
        dim_x = dim
        dim_y = dim
    elif shape == "lr":
        dim_x = dim
        dim_y = random.randint(dim, int(dim * 1.5))
    elif shape == "tr":
        dim_x = random.randint(dim, int(dim * 1.5))
        dim_y = dim

    set_of_chars = random.choice(["ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz",
                                 "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", "abcdefghijklmnopqrstuvwxyz0123456789"])

    # actually start drawing the image
    x_outer_padding = random.randint(10, 20)
    y_outer_padding = random.randint(10, 20)
    img = Image.new("RGB", (
        dim_x * (font_size + padding * 2) + x_outer_padding,
        dim_y * (font_size + padding * 2) + y_outer_padding
    ), color="white")

    font = ImageFont.truetype(font="fonts/" + random.choice(
        os.listdir("fonts/")), size=font_size)
    draw = ImageDraw.Draw(img)

    rand = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
                   for i in range(3))
    (font_name, case) = font.getname()
    name = f"{rand}-{type}_{shape}_{dim_x}x{dim_y}_{font_size}px_{padding}px_{font_name}"

    file = open(f"{dir}/labels/{category}/{name}.txt", "w")

    for x in range(dim_x):
        for y in range(dim_y):
            text = random.choice(set_of_chars)
            x_coord = x * (font_size + padding * 2) + x_outer_padding
            y_coord = y * (font_size + padding * 2) + y_outer_padding

            bb = draw.textbbox((x_coord, y_coord), text,
                               font=font)
            (bbx, bby, w, h) = convert(img.size, bb)

            file.write(
                f"{char_to_int_map[text if text.isdigit() else text.upper()]} {bbx} {bby} {w} {h}\n")
            # draw.rectangle(bb, outline="green")
            draw.text((x_coord, y_coord), text, font=font, fill="black")

    img.save(f"{dir}/images/{category}/{name}.jpg")
    file.close()


if __name__ == "__main__":
    random.seed(time.time())

    argparse = argparse.ArgumentParser(description="ballin")
    argparse.add_argument('--amt', type=int, default=100,
                          help="amount of images to generate")
    args = argparse.parse_args()
    amt = args.amt

    # make dirs
    if not os.path.exists("generated"):
        os.makedirs("generated")

    name = str(int(time.time())) + time.strftime("%m-%d-%Y") + \
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
    plt.figure()
    plt.subplot(121)
    plt.bar(list(sizes.keys()), list(sizes.values()), tick_label=["small", "medium", "large"],
            width=0.7, color=["blue", "green", "red"])
    plt.title("Size")
    plt.ylabel("Amount")

    plt.subplot(122)
    plt.bar(list(shapes.keys()), list(shapes.values()), tick_label=["square", "long rect", "short rect"],
            width=0.7, color=["blue", "green", "red"])
    plt.title("Shape")
    plt.ylabel("Amount")

    plt.savefig(f"{dir}/stats.jpg")
    plt.show()