import requests
import os
import time
import random

def download_image(url, path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(path, 'wb') as img_file:
            img_file.write(response.content)
        return True
    return False

# 确定文件和图像保存目录存在
if not os.path.exists('images'):
    os.makedirs('images')

# 读取卡牌的信息
with open('cards.txt', 'r') as file:
    lines = file.readlines()

# 处理每一行
for line in lines:
   # 从每一行中提取集合代码和卡牌编号
    card_name = line.strip()
    if(os.path.exists(f'images/{card_name}.png') or os.path.exists(f'images/{card_name}_face1.png') or os.path.exists(f'images/{card_name}_face2.png')):
        print(f'Image for {card_name} already exists.')
        continue
    
    # 在请求前添加随机延迟
    time.sleep(random.uniform(0.05, 0.1)) # 随机延迟50到100毫秒

    # 构建API URL
    url = f'https://api.scryfall.com/cards/named?fuzzy={card_name}'

    # 从API获取卡牌信息
    response = requests.get(url)

    # 检查响应状态
    if response.status_code == 200:
        card_info = response.json()
        if 'name' in card_info:
            en_name = card_info['name']
            time.sleep(random.uniform(0.05, 0.1))
            print(en_name)
            url = f'https://api.scryfall.com/cards/named?fuzzy={en_name}'
            response = requests.get(url)
            # 检查响应状态
            if response.status_code == 200:
                card_info = response.json()
                # 首先尝试下载image_uris中的图像
                if 'image_uris' in card_info and 'art_crop' in card_info['image_uris']:
                    if download_image(card_info['image_uris']['art_crop'], f'images/{card_name}.png'):
                        print(f'PNG image for {card_name} saved successfully.')
                        continue

                # 如果image_uris下载失败或不可用，检查和下载card_faces中的图像
                if 'card_faces' in card_info:
                    for i, face in enumerate(card_info['card_faces']):
                        if 'image_uris' in face and 'art_crop' in face['image_uris']:
                            image_url = face['image_uris']['art_crop']
                            if download_image(image_url, f'images/{card_name}_face{i+1}.png'):
                                print(f'PNG image for {card_name}, face {i+1} saved successfully.')
                            else:
                                print(f'Failed to download PNG image for {card_name}, face {i+1}.')
                else:
                    print(f'No PNG image found for {card_name}.')
            else:
                print(f'Failed to get card data for {card_name}.')
    else:
        print(f'Failed to get card data for {card_name}.')

print('Card image download script completed.')