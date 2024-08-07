import requests
import os
import time
import random



# 读取卡牌的信息
with open('cards.txt', 'r' , encoding='utf-8') as file:
    lines = file.readlines()

# 处理每一行
for line in lines:
    # 从每一行中提取集合代码和卡牌编号
    cn_name = line.strip()
    
    # 在请求前添加随机延迟
    time.sleep(random.uniform(0.05, 0.1)) # 随机延迟50到100毫秒

    # 构建API URL
    url = f'https://api.scryfall.com/cards/named?fuzzy={cn_name}'

    # 从API获取卡牌信息
    response = requests.get(url)

    # 检查响应状态
    if response.status_code == 200:
        card_info = response.json()
        
        # 获取卡牌名称
        if 'name' in card_info:
            card_name = card_info['name']
            # 存储到name.txt中
            with open('en_name.txt', 'a') as name_file:
                name_file.write(card_name + '\n')
                print(f'Card name "{card_name}" saved successfully.')
        else:
            print(f'No name found for {cn_name}.')
    else:
        print(f'Failed to get card data for {cn_name}.')

print('Card name extraction script completed.')
