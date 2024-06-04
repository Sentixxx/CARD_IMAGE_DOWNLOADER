from PIL import Image, ImageStat, ImageDraw
import os
import configparser
import numpy as np

# 配置文件路径及读取
cwd = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(cwd, 'config.ini'))
cfg = config["DEFAULT"]

# 指定加载图片的文件夹和输出图片的文件夹
input_folder = cfg.get("output_dir")
output_folder = cfg.get("bleed_out_dir")
fail_folder = cfg.get("fail_dir")
bleed_edge = cfg.getint("bleed_edge")
force = cfg.getboolean("force")

def mm_to_inches(mm):
    return mm / 25.4

# inch 到 pixel 的转换和图片的inch大小
inch_to_pixel = mm_to_inches(3)
img_width_inch = 2.48
img_height_inch = 3.46



# 黑色检测阈值
black_threshold = 25
# 圆角半径及边缘宽度的像素计算
corner_radius_mm = 3
edge_width_mm = 2.5
dpi = 300
corner_radius_pixel = int(dpi * corner_radius_mm / 25.4)
edge_width_pixel = int(dpi * edge_width_mm / 25.4)

# 确保输出文件夹和fail文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

if not os.path.exists('fail'):
    os.makedirs('fail')



# 检查是否为黑色
def is_black(color, threshold):
    return all(c <= threshold for c in color[:3])



#获取最多的颜色
def get_dominant_color(img, edge_width, corner_radius):
    width, height = img.size
    img = img.crop((width - edge_width, corner_radius, width, height - corner_radius))
    img = img.convert('RGBA')
    img = img.resize((1, 1))
    most_color = img.getpixel((0, 0))
    return most_color
# 检测图片四边是否有大量不为黑色的像素
def check_edge_colors(img, threshold, edge_width, corner_radius):
    if force:
        return False
    
    width, height = img.size

    # 顶部边缘
    top_edge = img.crop((corner_radius, 0, width - corner_radius, edge_width))
    top_colors = np.array(top_edge).reshape(-1, 4)
    top_black_pixels = sum(is_black(color, threshold) for color in top_colors)
    
    # 底部边缘
    bottom_edge = img.crop((corner_radius, height - edge_width, width - corner_radius, height))
    bottom_colors = np.array(bottom_edge).reshape(-1, 4)
    bottom_black_pixels = sum(is_black(color, threshold) for color in bottom_colors)


    # 左边缘
    left_edge = img.crop((0, corner_radius, edge_width, height - corner_radius))
    left_colors = np.array(left_edge).reshape(-1, 4)
    left_black_pixels = sum(is_black(color, threshold) for color in left_colors)

    # 右边缘
    right_edge = img.crop((width - edge_width, corner_radius, width, height - corner_radius))
    right_colors = np.array(right_edge).reshape(-1, 4)
    right_black_pixels = sum(is_black(color, threshold) for color in right_colors)

    # 黑色像素总和
    total_black_pixels = top_black_pixels + bottom_black_pixels + left_black_pixels + right_black_pixels
    total_pixels = len(top_colors) + len(bottom_colors) + len(left_colors) + len(right_colors)

    # 检查黑色像素占比
    black_pixel_ratio = total_black_pixels / total_pixels
    print(f"黑色像素占比：{black_pixel_ratio:.2f}")
    return black_pixel_ratio < 0.8  # 如果黑色像素小于50%，则视为大量不为黑色的像素

# 获取四个角的颜色
def get_corner_color(img, corner_size):
    width, height = img.size
    top_left = tuple(round(c) for c in ImageStat.Stat(img.crop((0, 0, corner_size, corner_size))).mean[:3])
    top_right = tuple(round(c) for c in ImageStat.Stat(img.crop((width - corner_size, 0, width, corner_size))).mean[:3])
    bottom_left = tuple(round(c) for c in ImageStat.Stat(img.crop((0, height - corner_size, corner_size, height))).mean[:3])
    bottom_right = tuple(round(c) for c in ImageStat.Stat(img.crop((width - corner_size, height - corner_size, width, height))).mean[:3])
    return top_left, top_right, bottom_left,bottom_right

# 遍历指定文件夹中的所有图片
for img_name in os.listdir(input_folder):
    if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(input_folder, img_name)
        print("正在处理图片：", img_path)
        with Image.open(img_path).convert("RGBA") as img:
            if check_edge_colors(img, black_threshold, edge_width_pixel, corner_radius_pixel):
                fail_path = os.path.join('fail/', img_name)
                img.save(fail_path)
                print(f"图片 {img_name} 被移至 fail 文件夹，由于边缘颜色检测失败。")
                continue

            # 计算图片的DPI
            pixel_width, pixel_height = img.size
            dpi_x = pixel_width / img_width_inch
            dpi_y = pixel_height / img_height_inch

            # 计算英寸对应的像素数
            bleed_pixel_width = int(dpi_x * inch_to_pixel)
            bleed_pixel_height = int(dpi_y * inch_to_pixel)
            most_color = (255, 255, 255, 255)
            if not force:
                corners = [
                    (0, 0),  # 左上角
                    (img.width - bleed_pixel_width, 0),  # 右上角
                    (0, img.height - bleed_pixel_height),  # 左下角
                    (img.width - bleed_pixel_width, img.height - bleed_pixel_height)  # 右下角
                ]

                most_color = get_dominant_color(img, edge_width_pixel, corner_radius_pixel)

                #修改圆角为方角
                print(most_color)
                for corner in corners:
                    x, y = corner
                    img.paste(most_color, (x, y, x + corner_radius_pixel, y + corner_radius_pixel))
                    img.paste(most_color, (x + bleed_pixel_width - corner_radius_pixel, y, x + bleed_pixel_width, y + corner_radius_pixel))
                    img.paste(most_color, (x, y + bleed_pixel_height - corner_radius_pixel, x + corner_radius_pixel, y + bleed_pixel_height))
                    img.paste(most_color, (x + bleed_pixel_width - corner_radius_pixel, y + bleed_pixel_height - corner_radius_pixel, x + bleed_pixel_width, y + bleed_pixel_height))


            # 创建新的图片，尺寸为原图加上bleed edge的部分
            new_width = img.width + 2 * bleed_pixel_width
            new_height = img.height + 2 * bleed_pixel_height
            new_img = Image.new("RGBA", (new_width, new_height),most_color)

            # 填充四个边
            new_img.paste(img.crop((corner_radius_pixel, 0, img.width - corner_radius_pixel, 1)).resize((new_width, bleed_pixel_height)), (0, 0))
            new_img.paste(img.crop((corner_radius_pixel, img.height - 1, img.width - corner_radius_pixel, img.height)).resize((new_width, bleed_pixel_height)), (0, new_height - bleed_pixel_height))
            new_img.paste(img.crop((0, corner_radius_pixel, 1, img.height - corner_radius_pixel)).resize((bleed_pixel_width, new_height)), (0, 0))
            new_img.paste(img.crop((img.width - 1, corner_radius_pixel, img.width, img.height - corner_radius_pixel)).resize((bleed_pixel_width, new_height)), (new_width - bleed_pixel_width, 0))



            # 将原图粘贴到新图的中心
            new_img.paste(img, (bleed_pixel_width, bleed_pixel_height))

            # 保存处理后的图片到输出文件夹
            output_path = os.path.join(output_folder, img_name)
            new_img.save(output_path)

print("图片处理完成。")
