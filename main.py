import requests
from secret import yd_token
import json
import os
import io
from pprint import pprint

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
        
        self._file_links.append(f'{create_url(self.url, path)}')
        
        return
    
    def create_info_json(self):
        resp = None
        file_info = {}
        
        for path in self._file_links:
            params = {'path': path}
            
            try:
                resp = requests.get(
                    path,
                    headers=self.headers,
                    params=params,
                    timeout=10
                )
                resp.raise_for_status()
            
            except requests.exceptions.RequestException as e:
                print(f'{handle_exceptions(e, resp)}')
                continue
            
            data = resp.json()
            file_info['name'] = {
                'path': data['path'],
                'size': data['size'],
                'url': path
            }
        
        with open('file_info.json', 'w') as f:
            json.dump(file_info, f, ensure_ascii=False, indent=2)
        
        return
    
    def get_last_upl(self):
        


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
            
            return f'Скачано {len(self.sub_breed_data)} из {len(sub_breed_list)} под пород'
        
        except requests.exceptions.RequestException as e:
            return handle_exceptions(e, resp)


def dz():
    #variables
    _text = input('Введите текст для котика: ')
    _group = input('Введите название группы: ')
    _breed = input('Введите название породы песеля: ')
    
    # get cat pic
    cat_call = cats_API()
    pic = cat_call.get_pic_w_text(_text)
    
    # save cat pic obj
    pic_obj = io.BytesIO(pic)
    
    # get dogs_sub_breeds
    dog_call = dogs_API(_breed)
    dog_call.get_subbreed()
    
    # create folders
    yd_call = yd_API(yd_token)
    yd_call.create_folder(_group)
    yd_call.create_folder(_breed)
    
    # work with YD files
    # cat pic upl
    yd_call.add_file(f'{_group}/{_text}', pic_obj)
    
    # dogs pic upl
    for s_breed in dog_call.sub_breed_data.values():
        yd_call.add_file(f'{_breed}/{s_breed["file_name"]}', s_breed['img'])

    # yd_call.create_info_json()
    


def main():
    dz()

main()