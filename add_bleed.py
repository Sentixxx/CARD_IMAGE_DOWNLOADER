from PIL import Image
import os
import configparser

cwd = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(cwd,'config.ini'))
cfg = config["DEFAULT"]
# 指定加载图片的文件夹和输出图片的文件夹
input_folder = cfg.get("card_source")
output_folder = cfg.get("bleed_out_dir")
bleed_edge = cfg.getint("bleed_edge")


inch_to_pixel = 0.12
# 假设给定的图片inch为2.48*3.46，即图片大小
img_width_inch = 2.48
img_height_inch = 3.46
# 确保输出文件夹存在
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# 遍历指定文件夹中的所有图片
for img_name in os.listdir(input_folder):
    if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(input_folder, img_name)
        print("正在处理图片：", img_path)
        with Image.open(img_path) as img:
            # 计算图片的DPI
            pixel_width, pixel_height = img.size

            # 计算DPI
            dpi_x = pixel_width / img_width_inch
            dpi_y = pixel_height / img_height_inch

            # 计算0.12英寸对应的像素数
            bleed_pixel_width = int(dpi_x * inch_to_pixel)
            bleed_pixel_height = int(dpi_y * inch_to_pixel)

            # 创建新的图片，尺寸为原图加上bleed edge的部分
            new_width = img.width + bleed_edge * bleed_pixel_width
            new_height = img.height + bleed_edge * bleed_pixel_height
            new_img = Image.new('RGB', (new_width, new_height), "black")

            # 将原图粘贴到新图的中心
            new_img.paste(img, (bleed_pixel_width, bleed_pixel_height))

            # 保存处理后的图片到输出文件夹
            output_path = os.path.join(output_folder, img_name)
            new_img.save(output_path)

print("图片处理完成。")