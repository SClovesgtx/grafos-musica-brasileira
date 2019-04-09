from py2neo import Graph

import os
import json

NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
graph = Graph("bolt://localhost:7687/db/data/", user="neo4j", password=NEO4J_PASSWORD)

def trataString(string):
    nova_string = string.replace("\"", '').replace("\'", '').strip()
    return nova_string

def CreateAlbum(album):
    nome_album = trataString(album['album'])
    query_album = "MERGE (:Álbum{nome_album:'%s', caracteristica:'%s',\
          formatos: '%s', primeiro_disco:'%s'})"%(nome_album,
                                                  album['info_album']['Característica'],
                                                  album['info_album']['Formatos'],
                                                  album['info_album']['Primeiro disco'])

    graph.run(query_album)

def CreateGravadora(album):
    gravadora = trataString(album['info_album']['Gravadora'])
    query_gravadora = "MERGE (:Gravadora{nome_gravadora:'%s'})"%(gravadora)
    graph.run(query_gravadora)

def CreateRelacaoAlbumGravadora(album):
    query_relacao = "MATCH (a:Álbum{nome_album:'%s'}), (g:Gravadora{nome_gravadora:'%s'}) \
         CREATE UNIQUE (a)-[:GRAVADO_EM]->(g)"%(trataString(album['album']),
                                                trataString(album['info_album']['Gravadora']))
    graph.run(query_relacao)

def createRelacaoProdutorAlbum(produtor, nome_album):
    graph.run('MATCH (p:Produtor{nome_produtor:"%s"}), (a:Álbum{nome_album:"%s"}) \
           CREATE UNIQUE (p)-[:PRODUZIU]->(a)'%(produtor, nome_album))

def CreateProdutores(album):
    if album['info_album'].get('Produtor'):
        querys_produtor = [("MERGE (:Produtor{nome_produtor:'%s'})"%(trataString(produtor)),
                            trataString(produtor))
                            for produtor in album['info_album']['Produtor'].split('/')]
        for query, produtor in querys_produtor:
            graph.run(query)
            createRelacaoProdutorAlbum(produtor, trataString(album['album']))

def CreateMusica(musica):
    graph.run('MERGE (:Música{nome_musica:"%s"})'%(musica))

def CreateRelacaoMusicaAlbum(musica, album, item):
    query = "MATCH (musica:Música{nome_musica:'%s'}), (album:Álbum{nome_album:'%s'}) \
         CREATE UNIQUE (musica)-[:PRESENTE{faixa:'%s'}]->(album)"%(musica, album, item)
    graph.run(query)

def CreateCompositores(compositores):
    for compositor in compositores:
        graph.run('MERGE (:Compositor{nome_compositor:"%s"})'%(trataString(compositor)))

def CreateRelacaoCompositoresMusica(compositores, musica):
    for compositor in compositores:
        graph.run('MATCH (c:Compositor{nome_compositor:"%s"}), (m:Música{nome_musica:"%s"}) \
                      CREATE UNIQUE (c)-[:COMPOS]->(m)'%(trataString(compositor), trataString(musica)))

def CreateRelacaoMusicoMusica(nome_musico, musica, nome_album, instrumento):
    query = "MATCH (musico:Músico{nome_musico:'%s'}), (musica:Música{nome_musica:'%s'}) \
            CREATE UNIQUE (musico)-[:TOCOU{album:'%s', instrumento:'%s'}]->(musica)"%(nome_musico,
                                                                                      musica,
                                                                                      nome_album,
                                                                                      instrumento)
    graph.run(query)

def CreateRelacaoMusicoAlbum(nome_musico, nome_album, item):
    query = "MATCH (musico:Músico{nome_musico:'%s'}), (album:Álbum{nome_album:'%s'}) \
            CREATE UNIQUE (musico)-[:PARTICIPOU{faixa:'%s'}]->(album)"%(nome_musico, nome_album, item)

    graph.run(query)

def CreateMusicos(musicos_da_faixa, musica, nome_album, item):
    musica = trataString(musica)
    nome_album =trataString(nome_album)
    for musico_participante in musicos_da_faixa:
        nome_musico, instrumento = [string.strip() for string in
                                    musico_participante.split(':')]
        nome_musico = trataString(nome_musico)
        graph.run('MERGE (:Músico{nome_musico:"%s"})'%(nome_musico))
        CreateRelacaoMusicoMusica(nome_musico, musica, nome_album, instrumento)
        CreateRelacaoMusicoAlbum(nome_musico, nome_album, item)

def CreateFaixas(faixas, album):
    for item in faixas:
        faixa_album = album['faixas'][item]
        for musica in faixa_album['musica']:
            musica = trataString(musica)
            CreateMusica(musica)
            CreateRelacaoMusicaAlbum(musica, trataString(album.get('album')), item)
            compositores = album.get('compositores')
            if compositores:
                CreateCompositores(compositores)
                CreateRelacaoCompositoresMusica(compositores, musica)
            CreateMusicos(faixa_album.get('musicos'), musica, album.get('album'), item)

def deleteAllData():
    query = "MATCH (node) OPTIONAL MATCH (node)-[rel]-() DELETE node, rel"
    graph.run(query)

def main():
    deleteAllData()
    with open('data.json', 'r', encoding='utf8') as f:
        data = json.load(f)

    for album in data:
        CreateAlbum(album)
        CreateGravadora(album)
        CreateRelacaoAlbumGravadora(album)
        CreateProdutores(album)
        faixas = album.get('faixas')
        CreateFaixas(faixas, album)

if __name__=='__main__':
    main()
