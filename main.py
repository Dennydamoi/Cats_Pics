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
        self.headers = {'Authorization': f'OAuth {self.token}'}
    
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
            # print(f"Upload status: {up_resp.status_code}")
        return {
            'file_name': os.path.basename(path),
            'path': path,
            'size': os.path.getsize(content)
        }


class dogs_API:
    
    def __init__(self, breed):
        self.breed = breed
        self.url = f'https://dog.ceo/api/breed/{breed}/'
        self.sub_breed_data = {}
        self._list_files = []
    
    def get_breed(self):
        try:
            resp = requests.get(create_url(self.url, 'images'), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            message = data.get('message', '')
            
            if message:
                return True, 'Порода существует'
            return False, 'Нет данный о породе'
            
        except requests.exceptions.Timeout:
            return False, 'Таймаут'
    
        except requests.exceptions.HTTPError:
            return False, f'Ошибка: {resp.status_code}'
    
        except requests.exceptions.RequestException as e:
            return False, f'Ошибка соединения: {e}'
    
    def get_subbreed(self):
        check_success, check_msg = self.get_breed()
        
        if not check_success:
            return check_msg
        
        try:
            resp = requests.get(create_url(self.url, 'list'), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            sub_breed_list = data.get('message', [])
            
            if not sub_breed_list:
                return 'Нет под пород'
            
            for s_breed in sub_breed_list:
                try:
                    resp = requests.get(create_url(self.url, f'{s_breed}/images/random'), timeout=10)
                    resp.raise_for_status()
                    
                    data = resp.json()
                    url = data['message']
                    file_name = url.split('/')[-1]
                    
                    img_resp = requests.get(url, timeout=10)
                    img_resp.raise_for_status()
                    
                    self.sub_breed_data[s_breed] = {
                        'img': img_resp.content,
                        'file_name': file_name
                    }
                
                except requests.exceptions.Timeout:
                    print('Таймаут')
                    continue
                except requests.exceptions.HTTPError:
                    print(f'Ошибка: {resp.status_code}')
                    continue
                except requests.exceptions.RequestException as e:
                    print(f'Ошибка соединение: {e}')
                    continue
            
            return f'Скачано {len(self.sub_breed_data)} из {len(sub_breed_list)} под пород'
        
        except requests.exceptions.Timeout:
            return 'Таймаут'
        except requests.exceptions.HTTPError:
            return f'Ошибка: {resp.status_code}'
        except requests.exceptions.RequestException as e:
            return f'Ошибка соединение: {e}'

    def create_pics(self):
        if self.sub_breed_data:
            for s_breed in self.sub_breed_data.values():
                with open(f'{s_breed["file_name"]}', 'wb') as f:
                    f.write(s_breed['img'])
                self._list_files.append(f'{s_breed["file_name"]}')


def dz():
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
    
    dog_call = dogs_API('hound')
    dog_call.get_subbreed()
    dog_call.create_pics()
    yd_call.create_folder('hound')
    for file in dog_call._list_files:
        print(f'{file.removesuffix(".jpg")}')
        yd_call.add_file(f'hound/{file.removesuffix(".jpg")}', f'{file}')
    
    
    with open('file_info.json', 'w', encoding='utf-8') as f:
        json.dump(file_info, f, indent=2, ensure_ascii=False)
    
    print(f'Файл загружен - {file_info}')
    print(f'Информация сохранена в file_info.json')

def main():
    dz()
    # dog_call = dogs_API('hound')
    # result = dog_call.get_subbreed()
    # print(f'{len(dog_call.sub_breed_data)}')
    # for breed_name, data in dog_call.sub_breed_data.items():
    #     print(f"\n{breed_name}:")
    #     print(f"  Имя файла: {data.get('file_name', 'НЕТ')}")
    #     print(f"  Размер img: {len(data.get('img', b''))} байт")
    #     print(f"  Первые 50 байт: {data.get('img', b'')[:50]}")
    
    # print(dog_call.sub_breed_data.keys())
    

main()