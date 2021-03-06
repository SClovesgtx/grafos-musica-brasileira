from py2neo import Graph
import argparse
import os
import json


def StringTreatment(string):
    if string:
        new_string = string.replace("\"", '').replace("\'", '').strip()
        return new_string

def CreateAlbum(album):
    name = album.get('album')
    name = StringTreatment(name) if album else 'no information'
    carac = album['info_album'].get('Característica')
    carac = StringTreatment(carac) if carac else 'no information'
    format = album['info_album'].get('Formatos')
    format = StringTreatment(format) if format else 'no information'
    year = album['info_album'].get('Primeiro disco')
    year = year if year else 'no information'

    query_album = "MERGE (:album{name:'%s', characteristic:'%s',\
          formats: '%s', first_disc:'%s'})"%(name,
                                            carac,
                                            format,
                                            year)

    graph.run(query_album)

def CreateGravadora(album):
    gravadora = StringTreatment(album['info_album']['Gravadora'])
    query_gravadora = "MERGE (:record_company{name:'%s'})"%(gravadora)
    graph.run(query_gravadora)

def CreateRelacaoAlbumGravadora(album):
    query_relacao = "MATCH (a:album{name:'%s'}), (c:record_company{name:'%s'}) \
         CREATE UNIQUE (a)-[:RECORDED_ON]->(c)"%(StringTreatment(album['album']),
                                                StringTreatment(album['info_album']['Gravadora']))
    graph.run(query_relacao)

def CreatePessoa(nome_pessoa):
    graph.run('MERGE (:person{name:"%s"})'%(nome_pessoa))

def createRelacaoProdutorAlbum(nome_produtor, nome_album):
    graph.run('MATCH (p:person{name:"%s"}), (a:album{name:"%s"}) \
           CREATE UNIQUE (p)-[:WAS_PRODUCER]->(a)'%(nome_produtor, nome_album))

def CreateProdutores(album):
    produtores = album['info_album'].get('Produtor')
    nome_album = StringTreatment(album['album'])
    if produtores:
        for produtor in produtores.split('/'):
            produtor = StringTreatment(produtor)
            CreatePessoa(produtor)
            createRelacaoProdutorAlbum(produtor, nome_album)

def CreateMusica(musica):
    graph.run('MERGE (:song{name:"%s"})'%(musica))

def CreateRelacaoMusicaAlbum(musica, album, item):
    query = "MATCH (s:song{name:'%s'}), (a:album{name:'%s'}) \
         CREATE UNIQUE (s)-[:PRESENT_IN{track:'%s'}]->(a)"%(musica, album, item)
    graph.run(query)


def CreateRelacaoCompositoresMusica(compositores, musica):
    for compositor in compositores:
        compositor = StringTreatment(compositor)
        CreatePessoa(compositor)
        graph.run('MATCH (c:person{name:"%s"}), (s:song{name:"%s"}) \
                      CREATE UNIQUE (c)-[:COMPOSED]->(s)'%(compositor, musica))

def CreateRelacaoMusicoMusica(nome_pessoa, musica, nome_album, instrumento):
    query = "MATCH (musico:Pessoa{nome:'%s'}), (musica:Música{nome:'%s'}) \
            CREATE UNIQUE (musico)-[:PLAYED{album:'%s', instrument:'%s', special_participant:'no'}]->(musica)"%(nome_pessoa,
                                                                                      musica,
                                                                                      nome_album,
                                                                                      instrumento)
    graph.run(query)

# def CreateRelacaoMusicoAlbum(nome_musico, nome_album, instrumento):
#     query = "MATCH (m:person{name:'%s'}), (a:album{name:'%s'}) \
#             CREATE UNIQUE (m)-[:PARTICIPATED{as:'MUSICIAN', instrument:'%s'}]->(a)"%(nome_musico,
#                                                                  nome_album, instrumento)
#
#     graph.run(query)


def CreateMusicos(musicos_da_faixa, musica, nome_album, item):
    for musico_participante in musicos_da_faixa:
        nome_musico, *instrumento = [StringTreatment(string) for string in
                                    musico_participante.split(':')]

        instrumento = instrumento[0] if instrumento else 'no information'
        CreatePessoa(nome_musico)
        CreateRelacaoMusicoMusica(nome_musico, musica, nome_album, instrumento)
        # CreateRelacaoMusicoAlbum(nome_musico, nome_album, instrumento)

# def CreateRelacaoArranjadoresAlbum(arranjadores, nome_album):
#     for arranjador in arranjadores:
#         nome_arranjador = StringTreatment(arranjador)
#         query = "MATCH (arranger_musician:person{name:'%s'}), (a:album{name:'%s'}) \
#             CREATE UNIQUE (arranger_musician)-[:PARTICIPATED{as:'arranger musician'}]->(a)"%(nome_arranjador, nome_album)

#    graph.run(query)

def CreateRelacaoArranjadoresMusica(nome_musica, arranjadores, nome_album):
    for arranjador in arranjadores:
        nome_arranjador = StringTreatment(arranjador)
        CreatePessoa(nome_arranjador)
        query = "MATCH (a:person{name:'%s'}), (s:song{name:'%s'}) \
                CREATE UNIQUE (a)-[:DID_ARRANGEMENT{album:'%s'}]->(s)"%(nome_arranjador,
                                                                        nome_musica,
                                                                        nome_album)
        graph.run(query)

def CreateRelacaoParticipanteMusica(participantes_especiais, musica, nome_album):
    for participante in participantes_especiais:
        nome_musico = StringTreatment(participante)
        CreatePessoa(nome_musico)
        #CreateRelacaoMusicoAlbum(nome_musico, nome_album)
        query = "MATCH (musico:person{name:'%s'}), (musica:song{name:'%s'}) \
                CREATE UNIQUE (musico)-[:PLAYED{album:'%s', special_participant:'yes'}]->(musica)"%(nome_musico,
                                                                                          musica,
                                                                                          nome_album)
        graph.run(query)

def CreateFaixas(faixas, album):
    for item in faixas:
        faixa_album = album['faixas'][item]
        for musica in faixa_album['musica']:
            musica = StringTreatment(musica)
            nome_album = StringTreatment(album['album'])
            if musica.lower() == 'pot-pourri': # por enquanto estamos ignorando
                break

            CreateMusica(musica)
            CreateRelacaoMusicaAlbum(musica, nome_album, item)
            compositores = faixa_album.get('compositores')
            if compositores:
                CreateRelacaoCompositoresMusica(compositores, musica)
            musicos = faixa_album.get('musicos')
            if musicos:
                CreateMusicos(musicos, musica, nome_album, item)
            arranjadores = faixa_album.get('arranjadores')
            if arranjadores:
                CreateRelacaoArranjadoresMusica(musica,
                                                arranjadores,
                                                nome_album)
                # CreateRelacaoArranjadoresAlbum(musica,
                #                              arranjadores,
                #                              nome_album, item)
            participantes_especiais = faixa_album.get('participacaoEspecial')
            if participantes_especiais:
                CreateRelacaoParticipanteMusica(participantes_especiais,
                                                musica,
                                                nome_album)

def createInterpretes(interpretes, nome_album):
    for interprete in interpretes:
        if 'Diversos Intérpretes' in interprete:
            break
        interprete = StringTreatment(interprete)
        CreatePessoa(interprete)
        query = "MATCH (musico:person{name:'%s'}), (a:album{name:'%s'}) \
                CREATE UNIQUE (musico)-[:PARTICIPATED{as:'interpreter'}]->(a)"%(interprete,
                                                                            nome_album)

        graph.run(query)



def deleteAllData():
    query = "MATCH (node) OPTIONAL MATCH (node)-[rel]-() DELETE node, rel"
    graph.run(query)

def main():
    deleteAllData()
    with open('mpb-data-set.json', 'r', encoding='utf8') as f:
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
    parser = argparse.ArgumentParser(
                description='Louder of json data to neo4j database')

    parser.add_argument('-p', '--password', type=str, required=True,
                        help='The neo4j password')

    args = parser.parse_args()

    graph = Graph("bolt://localhost:7687/db/data/", user="neo4j", password=args.password)

    main()
