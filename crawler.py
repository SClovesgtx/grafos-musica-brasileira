import json
import time
import os
import sys
from collections import deque

import requests
from bs4 import BeautifulSoup


url_base = "http://www.discosdobrasil.com.br/discosdobrasil/consulta/consulta.php?IndiceFixo=&Conteudo=Disco&Procura=&FormularioAnterior=&Apartirde=0&NumeroItens=7325&Formulario=Exibir"

def save_json(lista):
    with open('data.json', 'w', encoding='utf8') as file:
        json.dump(lista, file, ensure_ascii=False)

def get_links_discos(url_base):
    source = requests.get(url_base)
    soup = BeautifulSoup(source.content,  "html.parser")
    source.close()
    links_discos = list(set(['http://www.discosdobrasil.com.br/discosdobrasil/consulta/' + \
                    a['href'] for a in soup.find_all('a', href=True) \
                    if 'Id_Disco' in a['href']]))
    for link in links_discos:
        print(link)
        print('\n')
    return links_discos

def get_albumName(soup):
    album = soup.find('p', attrs={'class':"destacadorealcadorecuado"})
    return album.text.strip()

def get_interpretes(soup):
    interpretes = [a.text.strip() for a in soup.find('p',
             attrs={'class': 'realcadorecuado'}).findChildren("a", recursive=True)]
    return interpretes

def get_infosDisco(soup):
    table = soup.find_all('table', attrs={'width': '460'})[2]

    chaves = [td.find("p", recursive=False).text.replace(':', '')
              for td in table.find_all('td', attrs={'width': '25%'})]

    valores = [td.find("p", recursive=False).text.strip()
           for td in table.find_all('td', attrs={'width': '75%'})]

    infos_disco = {chave:valor for chave, valor in zip(chaves, valores)}

    return infos_disco

def rangeFaixas(soup):
    tables = soup.find_all('table', {'width':"460",
                                 'border':"0",
                                 'align':"center",
                                 'cellpadding':"0",
                                 'cellspacing':"0",
                                 'bgcolor':"#FAF7D6"})
    indices = []
    for i in range(len(tables)):
        p = tables[i].find('p', {'class':"destacadorecuado"})
        if p != None and 'faixa' in p.text:
            indices.append(i)

    range_faixas = []
    n = indices[-1]
    for i in range(len(indices)):
        faixa = []
        if indices[i] < n:
            ind1, ind2 = indices[i], indices[i+1]
            faixa = tables[ind1:ind2]
            range_faixas.append(faixa)
        else:
            faixa = tables[n:]
            range_faixas.append(faixa)
    return range_faixas


def get_infoFaixa(range_faixa):
    musicos = []
    compositores = []
    musicas = []
    for table in range_faixa:
        a_ = table.find_all('a')
        p = table.find('p', {'class':"destacadorecuado"})
        for a in a_:
            if a != None and 'Id_Musica' in a['href']:
                musicas.append(a.text.strip())
            if a != None and 'Id_Musico' in a['href']:
                musico_instrumento = a.parent.text.strip()
                musicos.append(musico_instrumento)
            if a != None and 'Id_Compositor' in a['href']:
                compositor = a.text.strip()
                compositores.append(compositor)
        if p != None and 'faixa' in p.text:
            faixa = p.text.strip()

    dic = {'musica': musicas,
          'compositores': compositores,
          'musicos': musicos}
    return faixa, dic

def connect(link):
    try:
        r = requests.get(link)
        soup = BeautifulSoup(r.content, 'html.parser')
        r.close()
        return soup
    except requests.exceptions.ConnectionError:
        return False

def main(urls):
    albuns = []
    urls_deque = deque(urls)
    for link in urls:
        dic = dict()
        soup = connect(link)

        # lidando com problemas de conexão
        if soup == False:
            for i in range(3): # tentar de conectar 3 vezes
                time.sleep(10)
                soup = connect(link)
                if soup != False:
                    break
        if soup == False:
            with open('urls.txt', 'w') as file:
                for url in urls_deque:
                    file.write(url) # salvando os links que faltam

            print("\n\nURLs e Dados Salvos!\\n")

            sys.exit()

        dic['album'] = get_albumName(soup)
        dic['interpretes'] = get_interpretes(soup)
        dic['info_album'] = get_infosDisco(soup)
        dic['faixas'] = dict()
        range_faixas = rangeFaixas(soup)
        for range_ in range_faixas:
            faixa, info_faixa = get_infoFaixa(range_faixa=range_)
            dic['faixas'][faixa] = info_faixa

        albuns.append(dic)
        save_json(albuns)
        print(json.dumps(dic, indent=4, sort_keys=True, ensure_ascii=False))
        print('\n\n')
        urls_deque.popleft() # remover os link que já foi


if __name__ == '__main__':
    print("================================================================")
    print("================ CAPTURANDO LINKS DOS ÁLBUNS! ==================")
    print("================================================================")
    print("\n\n")
    if os.path.isfile('./urls.txt'):
        file = open('urls.txt', 'r')
        urls = [url[:-1]for url in file.readlines()]
        main(urls=urls)
    else:
        urls = get_links_discos(url_base)
        with open('urls.txt', 'w') as file:
            for url in urls:
                file.write(url)
        main(urls)
