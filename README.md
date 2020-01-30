# neo4jing
* [patterns](https://neo4j.com/docs/cypher-manual/current/syntax/patterns/)

start docker

    docker run --name neo4j -d --rm --publish=7474:7474 --publish=7687:7687 --volume=/home/gunther/tilo_data/neo4j/data:/data --env NEO4J_AUTH=neo4j/quneo4j --env NEO4J_dbms_memory_heap_max__size=5G neo4j
    
to reset password remove `neo4j/data/dbms/auth` 

create index over the node's (with Label: `Resource`) name-attribute `CALL db.index.fulltext.createNodeIndex('nodenames', ['Resource'], ['name'])`

* if one has a clean RDF-triple-file: `CALL semantics.liteOntoImport('file:///filename.owl','RDF/XML')`

* count nodes where name endswith `MATCH (n:Resource) WHERE n.name ENDS WITH 'Site>' RETURN COUNT(n)`
* certain uri pathes of length 4 `MATCH p=(x:Resource)-[*4]-() WHERE x.uri='<http://sws.geonames.org/6547429/>' RETURN p LIMIT 25`