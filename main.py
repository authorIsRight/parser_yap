# main.py
import re
from urllib.parse import urljoin
import logging

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from utils import get_response, find_tag
from constants import BASE_DIR, MAIN_DOC_URL 
from configs import configure_argument_parser, configure_logging
from outputs import control_output

def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    # response = session.get(whats_new_url)
    # response.encoding = 'utf-8'
    response = get_response(session, whats_new_url)
    if response is None:
        # Если основная страница не загрузится, программа закончит работу.
        return
    soup = BeautifulSoup(response.text, features='lxml')
    #main_div = soup.find('section', attrs={'id': 'what-s-new-in-python'})    
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    #div_with_ul = main_div.find('div', attrs={'class': 'toctree-wrapper'})   
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})     
    sections_by_python = div_with_ul.find_all('li', attrs={'class': 'toctree-l1'})

    # Добавьте в пустой список заголовки таблицы. 
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    for section in tqdm(sections_by_python):
        version_a_tag = section.find('a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        # Замените код загрузки страницы и установки кодировки 
        # на вызов функции get_response().
        # response = session.get(version_link)
        # response.encoding = 'utf-8'
        response = get_response(session, version_link)
        if response is None:
            # Если страница не загрузится, программа перейдёт к следующей ссылке.
            continue  
        soup = BeautifulSoup(response.text, features='lxml') 
        #h1 = soup.find('h1')
        h1 = find_tag(soup, 'h1')        
        dl = soup.find('dl')  
        dl_text = dl.text.replace('\n', ' ')
        results.append((version_link, h1.text, dl_text))

#    for row in results:
#        print(*row) 
    return results

def latest_versions(session):
    # response = session.get(MAIN_DOC_URL)
    # response.encoding = 'utf-8'
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    sidebar = soup.find('div', {'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All versions' in ul.text:
            a_tags = ul.find_all('a')
            break
        else:
            raise Exception('Ничего не нашлось')

    # Добавьте в пустой список заголовки таблицы. 
    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'

    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()       
        else:
            version, status = a_tag.text, ''
        results.append((link, version, status))
#    for row in results:
#        print(*row)     
    return results

def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    # response = session.get(downloads_url)
    # response.encoding = 'utf-8'
    response = get_response(session, downloads_url)
    if response is None:
        return
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
    logging.info(f'Архив был загружен и сохранён: {archive_path}') 

MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
}

def main():    
    # Запускаем функцию с конфигурацией логов.
    configure_logging()
    # Отмечаем в логах момент запуска программы.
    logging.info('Парсер запущен!')

    # Конфигурация парсера аргументов командной строки —
    # передача в функцию допустимых вариантов выбора.
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    # Считывание аргументов из командной строки.
    args = arg_parser.parse_args()
    # Получение из аргументов командной строки нужного режима работы.
    # Логируем переданные аргументы командной строки.
    logging.info(f'Аргументы командной строки: {args}')    
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()



    parser_mode = args.mode
    # Поиск и вызов нужной функции по ключу словаря.
    results = MODE_TO_FUNCTION[parser_mode](session)

    # Если из функции вернулись какие-то результаты,
    if results is not None:
        # передаём их в функцию вывода вместе с аргументами командной строки.
        control_output(results, args)
    # Логируем завершение работы парсера.
    logging.info('Парсер завершил работу.') 

if __name__ == '__main__':
    main()         