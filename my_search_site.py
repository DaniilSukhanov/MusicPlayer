import requests
import fake_useragent
from bs4 import BeautifulSoup

import Errors


class Search:
    def __init__(self):
        self.url = 'https://my.mp3ha.org'

    def search(self, title):
        """Генератор, который возращает href и названия медио файла."""
        url = f'{self.url}/search/{title}'
        user = fake_useragent.UserAgent().random
        header = {
            'user-agent': user
        }
        response = requests.get(url, headers=header)
        soup = BeautifulSoup(response.text, 'lxml')
        try:
            # список данных о каждой песни.
            list_music = soup.find('div', class_='idx2e this_search').find(
                'ul').find_all('li')
        except AttributeError:
            try:
                list_music = soup.find('div', class_='idx3d').find(
                    'ul').find_all('li')
            except AttributeError:
                raise Errors.ErrorCouldNotFind
        for element in list_music:
            # пропускаем не нужные данные.
            if len(element) == 3:
                continue
            list_div = element.find_all('div')
            # ссылка на скачивание.
            download_href = list_div[5].find('a').get('href')
            spans = list_div[2].find_all('span')
            # название песни.
            download_title = f'{spans[0].text} - {spans[1].text}'
            # если есть знаки, которые не должны быть в пути, то удаляем их.
            if set('"\\|?:<>/*') | set(download_title):
                for i in '"\\|?:<>/*':
                    download_title = download_title.replace(i, '')
            yield download_title, download_href


# скачивает по ссылке песню и дает имя.
def download(href, title):
    with open(f'base data/music/songs/{title}.mp3', 'wb') as file:
        file.write(requests.get(href).content)


if __name__ == '__main__':
    pass
