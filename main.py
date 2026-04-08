import requests
from secret import yd_token
import json
import os

def create_url(url, method):
    return f'{url}{method}'

class cats_API:
    url = 'https://cataas.com/'  
    
    def get_pic_w_text(self, text):
        response = requests.get(create_url(self.url, f'cat/says/:{text}'))
        return response.content


class yd_API:
    url = 'https://cloud-api.yandex.net/v1/disk/'
    
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'OAuth {token}'}
        
    def create_folder(self,path):
        params = {'path': f'{path}'}
        response = requests.put(create_url(self.url, f'resources'),
                                headers=self.headers,
                                params=params,
                                timeout=10
                                )
    
    def add_file(self, path, content):
        params = {'path': path}
        response = requests.get(create_url(self.url, f'resources/upload'),
                                headers=self.headers,
                                params=params,
                                timeout=10
                                )
        upl_link = response.json()['href']
        
        with open(content, 'rb') as f:
            up_resp = requests.put(upl_link, files={'file': f}, timeout=30)
            print(f"Upload status: {up_resp.status_code}")
        return {
            'file_name': os.path.basename(path),
            'path': path,
            'size': os.path.getsize(content)
        }

def main():
    _text = input('Введите текст:')
    
    # get pic
    cat_call = cats_API()
    pic = cat_call.get_pic_w_text(_text)
    
    # save pic
    with open(f'{_text}.png', 'wb') as f:
        f.write(pic)
    
    # create folder
    yd_call = yd_API(yd_token)
    yd_call.create_folder('Python 148')
    
    # work with files
    file_info = yd_call.add_file(f'Python 148/{_text}', f'{_text}.png')
    
    with open('file_info.json', 'w', encoding='utf-8') as f:
        json.dump(file_info, f, indent=2, ensure_ascii=False)
    
    print(f'Файл загружен - {file_info}')
    print(f'Информация сохранена в file_info.json')

main()