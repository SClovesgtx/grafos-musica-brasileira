![alt text](https://br.royalvegascasino.com/blogrvc/images/uploads/br_royalvegas_com/2018/10/destak_carictura.png)

# MPB and Graphs

This project aims to make possible the study of network structures, existing in Brazilian popular music, through the use of graphs and the neo4j database.

The data I have so far captured come from the website [Discos do Brasil](http://www.discosdobrasil.com.br/discosdobrasil/indice.htm). This website was created from personal collection of Maria Luiza Kfouri, a brazilian journalist and musicologist. There are more than 7 thousand records, 1,866 main performers, 44,652 songs, 16,049 musicians, 2,537 arrangers and 10,233 registered composers.

### How to upload data to Neo4j?

Install neo4j on your machine following [this](https://neo4j.com/docs/operations-manual/current/installation/) tutorial.

Install the required python packages by running the following command:

```
$ pip3 install -r requirements.txt
```

And then run the following command to upload the data to your local neo4j database:

```
$ python3 save2neo.py --password <your neo4j password here>
```
