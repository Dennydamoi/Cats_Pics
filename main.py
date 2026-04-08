import requests
from secret import token

class cats_API:
    url = 'https://cataas.com/'
    
    # def __init__(self, text):
    #     self.text = text
        
    
    def create_url(self,method):
        return f'{self.url}{method}'
    
    def get_pic_w_text(self, text):
        response = requests.get(self.create_url(f'cat/says/:{text}'))
        return response.content


