from PIL import Image, ImageStat, ImageDraw
import os
import configparser
import numpy as np
import tqdm

# 配置文件路径及读取
cwd = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(cwd, "config.ini"))
cfg = config["DEFAULT"]

# 指定加载图片的文件夹和输出图片的文件夹
input_folder = cfg.get("output_dir")
output_folder = cfg.get("bleed_out_dir")
fail_folder = cfg.get("fail_dir")
bleed_edge = cfg.getint("bleed_edge")
force = cfg.getboolean("force")


def mm_to_inches(mm):
    return mm / 25.4

def get_bleed_width():
    if cfg.get("bleed_mode") == "order":
        return mm_to_inches(3)
    else:
        return 0.125

# inch 到 pixel 的转换和图片的inch大小
inch_to_pixel = get_bleed_width()
img_width_inch = 2.48
img_height_inch = 3.46
corner_radius_mm = 2.5
# 黑色检测阈值
black_threshold = 45
# 圆角半径及边缘宽度的像素计算
edge_width_mm = 2.5
dpi = 300
corner_radius_pixel = int(dpi * corner_radius_mm / 25.4)
edge_width_pixel = int(dpi * edge_width_mm / 25.4)



# 检查是否为黑色
def is_black(color, threshold):
    return all(c <= threshold for c in color[:3])


def is_transparent(img):
    for i in range(img.height):
        for j in range(img.width):
            if img.getpixel((j, i))[3] == 0:
                return True
    return False


# 检测图片四边是否有大量不为黑色的像素
def check_edge_colors(img):
    if force:
        return False
    width, height = img.size
    # 检测四个边的颜色
    # 顶部
    top_edge = img.crop((width / 30, 0, width - width / 30, height / 80))
    top_colors = np.array(top_edge.getdata()).reshape(-1, 4)
    top_black_pixels = sum(is_black(color, black_threshold) for color in top_colors)

    # 底部
    bottom_edge = img.crop(
        (width / 30, height - height / 80, width - width / 30, height)
    )
    bottom_colors = np.array(bottom_edge.getdata()).reshape(-1, 4)
    bottom_black_pixels = sum(
        is_black(color, black_threshold) for color in bottom_colors
    )

    # 左边
    left_edge = img.crop((0, height / 100, width / 30, height - height / 100))
    left_colors = np.array(left_edge.getdata()).reshape(-1, 4)
    left_black_pixels = sum(is_black(color, black_threshold) for color in left_colors)

    # 右边
    right_edge = img.crop(
        (width - width / 30, height / 100, width, height - height / 100)
    )
    right_colors = np.array(right_edge.getdata()).reshape(-1, 4)
    right_black_pixels = sum(is_black(color, black_threshold) for color in right_colors)

    total_black_pixels = (
        top_black_pixels + bottom_black_pixels + left_black_pixels + right_black_pixels
    )
    total_pixels = (
        len(top_colors) + len(bottom_colors) + len(left_colors) + len(right_colors)
    )

    black_pixel_ratio = total_black_pixels / total_pixels
    print(f"黑色像素占比：{black_pixel_ratio:.2f}")
    return black_pixel_ratio < 0.6  # 如果黑色像素小于60%，则视为大量不为黑色的像素


def handle():
    # 确保输出文件夹和fail文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    if not os.path.exists("fail"):
        os.makedirs("fail")
    # 遍历指定文件夹中的所有图片
    print("开始处理图片...")
    print("图片输入文件夹：", input_folder)
    for img_name in tqdm.tqdm(os.listdir(input_folder)):
        if img_name.lower().endswith((".png", ".jpg", ".jpeg")):
            img_path = os.path.join(input_folder, img_name)
            print("正在处理图片：", img_path)
            with Image.open(img_path).convert("RGBA") as img:
                if check_edge_colors(img):
                    fail_path = os.path.join("fail/", img_name)
                    img.save(fail_path)
                    print(f"图片 {img_name} 被移至 fail 文件夹，由于边缘颜色检测失败。")
                    continue

                img.resize((1488, 2079), Image.LANCZOS)

                # 计算图片的DPI
                pixel_width, pixel_height = img.size
                dpi_x = pixel_width / img_width_inch
                dpi_y = pixel_height / img_height_inch

                # 计算英寸对应的像素数
                bleed_pixel_width = int(dpi_x * inch_to_pixel)
                bleed_pixel_height = int(dpi_y * inch_to_pixel)

                top = img.crop((0, 0, pixel_width, pixel_height / 80))
                top = top.resize((1, 1))

                bottom = img.crop(
                    (0, pixel_height - pixel_height / 80, pixel_width, pixel_height)
                )
                bottom = bottom.resize((1, 1))
                
                if not force or not is_transparent:
                    pixel_data = img.load()

                    color = top.getpixel((0, 0))

                    for i in range(pixel_height // 40):
                        for j in range(pixel_width):
                            # if pixel_data[j,i][3] == 0:
                            pixel_data[j, i] = bottom.getpixel((0, 0))

                    color = bottom.getpixel((0, 0))

                    for i in range(pixel_height - pixel_height // 40, pixel_height):
                        for j in range(pixel_width):
                            # if pixel_data[j,i][3] == 0:
                            pixel_data[j, i] = bottom.getpixel((0, 0))
                
                color = bottom.getpixel((0, 0))
                new_width = img.width + 2 * bleed_pixel_width
                new_height = img.height + 2 * bleed_pixel_height
                new_img = Image.new("RGBA", (new_width, new_height), color)

                for i in range(pixel_height // 2):
                    for j in range(pixel_width):
                        new_img.putpixel((j, i), top.getpixel((0, 0)))
                # # 将原图粘贴到新图的中心
                new_img.paste(img, (bleed_pixel_width, bleed_pixel_height))

                # # 保存处理后的图片到输出文件夹
                output_path = os.path.join(output_folder, img_name)
                new_img.save(output_path)

    print("图片处理完成。")


if __name__ == "__main__":
    handle()
