import requests
import os
import time
import random
import sys
import configparser
import re
import subprocess
import uuid
import tqdm

cwd = os.path.dirname(os.path.abspath(__file__))
config = configparser.ConfigParser()
config.read(os.path.join(cwd,'config.ini'))
cfg = config["DEFAULT"]
failed = []

def download_image(url, path, retries=3):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                base, extension = os.path.splitext(path)
                while os.path.exists(path):
                    print(f'Image for {path} already exists.')
                    path = f'{base}_{uuid.uuid4()}{extension}'
                with open(path, 'wb') as img_file:
                    img_file.write(response.content)
                print(f'Image for {path} saved successfully.')
                return True
            else:
                print(f'Failed to download image, status code: {response.status_code}.')
        except (requests.exceptions.RequestException, requests.exceptions.ChunkedEncodingError) as e:
            print(f'Error occurred: {e}, retrying {attempt + 1}/{retries}...')
    print(f'Failed to download image after {retries} attempts.')
    return False

def parse_mode():
    format_mappings = {
        "num": r"(\d+)",
        "name": r"([^()]+)",
        "set": r"\(([^)]+)\)",
        "no": r"([^\s]+)"
    }
    format_str = cfg.get("card_format")
    regex_parts = [format_mappings[part.strip()] for part in format_str.split()]
    regex = r'\s+'.join(regex_parts) + r'( \*\w\*)?'

    return regex , format_str

def read_info():
    src = cfg.get("card_source")
    with open(src, 'r',encoding='utf-8') as file:
        lines = file.readlines()
    return lines


def get_card_data():
    # 读取卡牌信息
    lines = read_info()
    regex , format_str = parse_mode()
    card_data = []
    for line in lines:
        line = line.strip()
        match = re.match(regex, line)
        if match:
            matched_groups = match.groups()
            card_entry = {}
            for i , part in enumerate(format_str.split()):
                card_entry[part] = matched_groups[i]
                if part == 'num':
                    card_entry[part] = int(card_entry[part])
                if part == 'set':
                    card_entry[part] = card_entry[part].lower()
            card_data.append(card_entry)
            #print(card_entry)

    return card_data

def get_card(card,mode,lang='en'):
    # 构建API URL
    if 'name' in card and not ('set' in card):
        url = f'https://api.scryfall.com/cards/named?fuzzy={card["name"]}'
        this_card = card["name"]
    else:
        url = f'https://api.scryfall.com/cards/{card["set"]}/{card["no"]}'
        this_card = f'{card["set"]} {card["no"]}'

    if lang == 'cs':
        url= f'https://api.scryfall.com/cards/search?order=released&dir=desc&q=name%3D{card["name"]}%20lang%3Dzhs'

    print(f'Processing {this_card}...')
    print(f'URL: {url}')
    # 在请求前添加随机延迟
    time.sleep(random.uniform(0.05, 0.1))
    # 从API获取卡牌信息
    response = requests.get(url)

    # 检查响应状态
    if response.status_code == 200:
        card_info = response.json()
        if lang == 'cs' and (response.json()["data"].__len__() != 1 or response.json()["data"][0]["name"].lower() != this_card.lower()):
            print('-----------------------------------------------')
            print(f'Failed to download PNG image for {this_card}.')
                    # failed.append(card)
            print('-----------------------------------------------')
            with open('failed_cards.txt', 'a') as file:
                file.write(this_card + '\n')
            get_card(card,mode)
            return
        if lang == 'cs':
            card_info = response.json()["data"][0]
        if 'num' in card:
            need = card["num"]
        else:
            need = 1
        # 首先尝试下载image_uris中的图像
        print(f'need:{need}')
        if 'image_uris' in card_info and mode in card_info['image_uris']:
            while need > 0:
                if download_image(card_info['image_uris'][mode], f'{output_dir}/{this_card}.png'):
                    print(f'PNG image for {this_card} saved successfully.')
                    need -= 1
                else:
                    print('-----------------------------------------------')
                    print(f'Failed to download PNG image for {this_card}.')
                    # failed.append(card)
                    print('-----------------------------------------------')
                    with open('failed_cards.txt', 'a') as file:
                        file.write(this_card + '\n')
                    break
            if need == 0:
                return
        # 如果image_uris下载失败或不可用，检查和下载card_faces中的图像
        if 'card_faces' in card_info:
            for i, face in enumerate(card_info['card_faces']):
                if 'image_uris' in face and mode in face['image_uris']:
                    image_url = face['image_uris'][mode]
                    while need > 0:
                        if this_card.find('/') != -1:
                            this_card = this_card.replace('/','-')
                        if download_image(image_url, f'{output_dir}/{this_card}_face{i+1}.png'):
                            print(f'PNG image for {this_card}, face {i+1} saved successfully.')
                            need -= 1
                        else:
                            print('-----------------------------------------------')
                            print(f'Failed to download PNG image for {this_card}, face {i+1}.')
                            with open('failed_cards.txt', 'a') as file:
                                file.write(this_card + '\n')
                            # failed.append(card)
                            print('-----------------------------------------------')
                            return
                    if need == 0 and i == 0:
                        if 'num' in card:
                            need = card["num"]
                        else:
                            need = 1
                        
        else:
            print('-----------------------------------------------')
            print(f'No PNG image found for {this_card}.')
            # failed.append(card)
            print('-----------------------------------------------')
            with open('failed_cards.txt', 'a') as file:
                    file.write(this_card + '\n')
    else:
        print('-----------------------------------------------')
        print(f'Failed to get card data for {this_card}.')
        # failed.append(card)
        print(f'Response code: {response.status_code}')
        print('-----------------------------------------------')
        with open('failed_cards.txt', 'a') as file:
            file.write(this_card + '\n')

def get_scryfall():
    cards = get_card_data()
    print(cards)
    mode = cfg.get("mode")
    for card in tqdm.tqdm(cards):
        get_card(card, mode , cfg.get("lang"))



        

if __name__ == '__main__':

    output_dir = cfg.get("output_dir")
    #确定文件和图像保存目录存在
    print(output_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 读取卡牌的信息

    get_scryfall()
    print('Card image download script completed.')

    if failed.__len__() > 0:
        with open('failed_cards.txt', 'w') as file:
            for card in failed:
                file.write(str(card) + '\n')

    if cfg.getboolean("add_bleed"):
        print('Bleeding cards...')
        subprocess.run(['python', 'add_bleed.py'])
        print('Card bleeding script completed.')
    