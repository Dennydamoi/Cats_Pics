import requests
import time
import json
import io
from secret import yd_token
from tqdm import tqdm

def create_url(url, method):
    return f'{url}{method}'


def handle_exceptions(e, response=None, YD=False):
    if isinstance(e, requests.exceptions.Timeout):
        return 'Таймаут'
    elif isinstance(e, requests.exceptions.HTTPError):
        if response is not None:
            return f'Ошибка {response.status_code}'
    elif isinstance(e, requests.exceptions.RequestException):
        return f'Ошибка соединения: {e}'
    return 'Неизвестная ошибка'


def format_size(bytes):
    for uni in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f'{bytes:.1f}{uni}'
        bytes /= 1024.0
    return f'{bytes:.1f} TB'


class cats_API:
    url = 'https://cataas.com/'  
    
    def get_pic_w_text(self, text):
        response = None
        
        try:
            response = requests.get(create_url(self.url, f'cat/says/{text}'), timeout=10)
            response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, response)
        
        return response.content


class yd_API:
    url = 'https://cloud-api.yandex.net/v1/disk/'
    
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'OAuth {self.token}'}
        self._file_links = []
    
    def create_folder(self,path):
        params = {'path': f'{path}'}
        response = None
        
        try:
            response = requests.put(create_url(self.url, f'resources'),
                                    headers=self.headers,
                                    params=params,
                                    timeout=10,
                                    )
            response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, response)
    
    def add_file(self, path, content):
        params = {'path': path}
        response = None
        up_resp = None
        
        try:
            response = requests.get(create_url(self.url, f'resources/upload'),
                                    headers=self.headers,
                                    params=params,
                                    timeout=10
                                    )
            response.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, response)
        except KeyError:
            return 'Ошибка: нет ссылки для загрузки'
        upl_link = response.json()['href']
        
        try:
            up_resp = requests.put(upl_link, files={'file': content}, timeout=30)
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, up_resp)
        
        self._file_links.append(f'{create_url("disk:/", path)}')
        
        return
    
    
    def get_last_upl(self, range):
        resp = None
        file_info = {}
        params = {
            'limit': range
        }
        
        try:
            resp = requests.get(
                create_url(self.url, f'resources/last-uploaded'),
                params= params,
                headers= self.headers,
                timeout= 10
            )
            resp.raise_for_status()
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, resp)
        
        data = resp.json()['items']
        
        for item in data:
            file_info[f'{item["name"]}'] = {
                'path': item['path'],
                'size': format_size(item['size'])
            }
        
        with open('file_info.json', 'w') as f:
            json.dump(file_info, f, ensure_ascii=False, indent=2)
        
        return


class dogs_API:
    
    def __init__(self, breed):
        self.breed = breed
        self.url = f'https://dog.ceo/api/breed/{self.breed}/'
        self.sub_breed_data = {}
        self._list_files = []
    
    def get_breed(self):
        resp = None
        
        try:
            resp = requests.get(create_url(self.url, 'images'), timeout=10)
            resp.raise_for_status()
            data = resp.json()
            message = data.get('message', '')
            
            if message:
                return True, 'Порода существует'
            return False, 'Нет данный о породе'
        
        except requests.exceptions.RequestException as e:
            return False, handle_exceptions(e, resp)
    
    def get_subbreed(self):
        check_success, check_msg = self.get_breed()
        
        if not check_success:
            return check_msg
        
        resp = None
        
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
                        'img': io.BytesIO(img_resp.content),
                        'file_name': f'{self.breed}_{s_breed}_{file_name}'
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
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, resp)
        
        return f'Скачано {len(self.sub_breed_data)} из {len(sub_breed_list)} под пород'


def dz():
    print("=" * 60)
    print("РЕЗЕРВНОЕ КОПИРОВАНИЕ НА ЯНДЕКС.ДИСК")
    print("=" * 60)
    
    #variables
    _text = input('Введите текст для котика: ')
    print()
    _group = input('Введите название группы: ')
    print()
    _breed = input('Введите название породы песеля: ')
    print()
    
    # get cat pic
    print('\n Загрузка картинки котика')
    cat_call = cats_API()
    pic = cat_call.get_pic_w_text(_text)
    
    # save cat pic obj
    pic_obj = io.BytesIO(pic)
    print('Котик готов')
    
    # get dogs_sub_breeds
    print(f'\n Загрузка данных о породе "{_breed}"')
    dog_call = dogs_API(_breed)
    result = dog_call.get_subbreed()
    
    if not result:
        print('Ошибка получения подпород')
        return
    
    print(result)
    
    # create folders
    print('\n Подключение к Яндекс Диску')
    yd_call = yd_API(yd_token)
    print(f'Создание папки {_group}')
    yd_call.create_folder(_group)
    print(f'Создание папки {_breed}')
    yd_call.create_folder(_breed)
    
    # work with YD files
    # cat pic upl
    print('\n Загрузга файлов...')
    print('\n Загрузка котика...')
    yd_call.add_file(f'{_group}/{_text}', pic_obj)
    print('Котик загружен')
    
    # dogs pic upl
    sub_breeds = list(dog_call.sub_breed_data.values())
    print(f'\n Загрузка {len(sub_breeds)} фото песелей')
    
    for s_breed in tqdm(sub_breeds, desc='Загрузка', unit='файл'):
        result = yd_call.add_file(f'{_breed}/{s_breed["file_name"]}', s_breed['img'])
        time.sleep(0.1)
    
    print(f'\n Загружено {len(sub_breeds)} файлов')
    
    # yd_call.create_info_json()
    print('\n Создаю file_info.json')
    yd_call.get_last_upl(len(yd_call._file_links))
    
    print("\n" + "=" * 60)
    print("РЕЗЕРВНОЕ КОПИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
    print(f"Всего загружено: {len(yd_call._file_links)} файлов")
    print(f"Информация: file_info.json")


def main():
    dz()
    
main()