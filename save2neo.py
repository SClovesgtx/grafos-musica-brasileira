from py2neo import Graph

import os
import json

NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
graph = Graph("bolt://localhost:7687/db/data/", user="neo4j", password=NEO4J_PASSWORD)

def trataString(string):
    if string:
        nova_string = string.replace("\"", '').replace("\'", '').strip()
        return nova_string

def CreateAlbum(album):
    nome = album.get('album')
    nome = trataString(nome) if album else 'sem informação'
    nome = trataString(album['album'])
    carac = album['info_album'].get('Característica')
    carac = trataString(carac) if carac else 'sem informação'
    formato = album['info_album'].get('Formatos')
    formato = trataString(formato) if formato else 'sem informação'
    ano = album['info_album'].get('Primeiro disco')
    ano = ano if ano else 'sem informação'

    query_album = "MERGE (:Álbum{nome:'%s', caracteristica:'%s',\
          formatos: '%s', primeiro_disco:'%s'})"%(nome,
                                                  carac,
                                                  formato,
                                                  ano)

    graph.run(query_album)

def CreateGravadora(album):
    gravadora = trataString(album['info_album']['Gravadora'])
    query_gravadora = "MERGE (:Gravadora{nome:'%s'})"%(gravadora)
    graph.run(query_gravadora)

def CreateRelacaoAlbumGravadora(album):
    query_relacao = "MATCH (a:Álbum{nome:'%s'}), (g:Gravadora{nome:'%s'}) \
         CREATE UNIQUE (a)-[:GRAVADO_EM]->(g)"%(trataString(album['album']),
                                                trataString(album['info_album']['Gravadora']))
    graph.run(query_relacao)

def CreatePessoa(nome_pessoa):
    graph.run('MERGE (:Pessoa{nome:"%s"})'%(nome_pessoa))

def createRelacaoProdutorAlbum(produtor, nome):
    graph.run('MATCH (p:Pessoa{nome:"%s"}), (a:Álbum{nome:"%s"}) \
           CREATE UNIQUE (p)-[:FOI_PRODUTOR]->(a)'%(produtor, nome))

def CreateProdutores(album):
    produtores = album['info_album'].get('Produtor')
    nome_album = trataString(album['album'])
    if produtores:
        for produtor in produtores.split('/'):
            produtor = trataString(produtor)
            CreatePessoa(produtor)
            createRelacaoProdutorAlbum(produtor, nome_album)

def CreateMusica(musica):
    graph.run('MERGE (:Música{nome:"%s"})'%(musica))

def CreateRelacaoMusicaAlbum(musica, album, item):
    query = "MATCH (musica:Música{nome:'%s'}), (album:Álbum{nome:'%s'}) \
         CREATE UNIQUE (musica)-[:PRESENTE{faixa:'%s'}]->(album)"%(musica, album, item)
    graph.run(query)


def CreateRelacaoCompositoresMusica(compositores, musica):
    for compositor in compositores:
        compositor = trataString(compositor)
        CreatePessoa(compositor)
        graph.run('MATCH (c:Pessoa{nome:"%s"}), (m:Música{nome:"%s"}) \
                      CREATE UNIQUE (c)-[:COMPOS]->(m)'%(compositor, musica))

def CreateRelacaoMusicoMusica(nome_pessoa, musica, nome_album, instrumento):
    query = "MATCH (musico:Pessoa{nome:'%s'}), (musica:Música{nome:'%s'}) \
            CREATE UNIQUE (musico)-[:TOCOU{album:'%s', instrumento:'%s'}]->(musica)"%(nome_pessoa,
                                                                                      musica,
                                                                                      nome_album,
                                                                                      instrumento)
    graph.run(query)

def CreateRelacaoMusicoAlbum(nome_musico, nome_album, item):
    query = "MATCH (musico:Pessoa{nome:'%s'}), (album:Álbum{nome:'%s'}) \
            CREATE UNIQUE (musico)-[:PARTICIPOU{faixa:'%s'}]->(album)"%(nome_musico,
                                                                        nome_album,
                                                                        item)

    graph.run(query)

def CreateMusicos(musicos_da_faixa, musica, nome_album, item):
    for musico_participante in musicos_da_faixa:
        nome_musico, instrumento = [trataString(string) for string in
                                    musico_participante.split(':')]

        CreatePessoa(nome_musico)
        CreateRelacaoMusicoMusica(nome_musico, musica, nome_album, instrumento)
        CreateRelacaoMusicoAlbum(nome_musico, nome_album, item)

def CreateFaixas(faixas, album):
    for item in faixas:
        faixa_album = album['faixas'][item]
        for musica in faixa_album['musica']:
            musica = trataString(musica)
            nome_album = trataString(album['album'])
            CreateMusica(musica)
            CreateRelacaoMusicaAlbum(musica, nome_album, item)
            compositores = album.get('compositores')
            if compositores:
                CreateRelacaoCompositoresMusica(compositores, musica)
            musicos = faixa_album.get('musicos')
            if musicos:
                CreateMusicos(musicos, musica, nome_album, item)

def deleteAllData():
    query = "MATCH (node) OPTIONAL MATCH (node)-[rel]-() DELETE node, rel"
    graph.run(query)

def main():
    # deleteAllData()
    with open('data.json', 'r', encoding='utf8') as f:
        data = json.load(f)

    for album in data:
        CreateAlbum(album)
        CreateGravadora(album)
        CreateRelacaoAlbumGravadora(album)
        CreateProdutores(album)
        faixas = album.get('faixas')
        if faixas:
            CreateFaixas(faixas, album)

if __name__=='__main__':
    main()
