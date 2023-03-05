# main.py
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from constants import BASE_DIR, MAIN_DOC_URL 
from configs import configure_argument_parser

def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = session.get(whats_new_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = soup.find('section', attrs={'id': 'what-s-new-in-python'})    

    div_with_ul = main_div.find('div', attrs={'class': 'toctree-wrapper'})    
    sections_by_python = div_with_ul.find_all('li', attrs={'class': 'toctree-l1'})

    results = []

    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = session.get(version_link) 
        response.encoding = 'utf-8' 
        soup = BeautifulSoup(response.text, features='lxml') 
        h1 = soup.find('h1')
        dl = soup.find('dl')  
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))

    for row in results:
        print(*row) 


def latest_versions(session):
    response = session.get(MAIN_DOC_URL)  
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = soup.find('div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')

    results = []
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()       
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
    for row in results:
        print(*row)     


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')

    response = session.get(downloads_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, features='lxml')
    main_tag = soup.find('div', {'role': 'main'})
    table_tag = main_tag.find('table', {'class': 'docutils'})     
    pdf_a4_tag = table_tag.find('a', {'href': re.compile(r'.+pdf-a4\.zip$')}) 
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link) 
    filename = archive_url.split('/')[-1] 
    print(archive_url)
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / filename 
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)     
        
MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
}

def main():    
    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()
    # Получение из аргументов командной строки нужного режима работы.
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()



    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)

if __name__ == '__main__':
    main()         