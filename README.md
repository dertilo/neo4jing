# neo4jing
* [patterns](https://neo4j.com/docs/cypher-manual/current/syntax/patterns/)

start docker

    docker run --name neo4j -d --rm --publish=7474:7474 --publish=7687:7687 --volume=/home/gunther/tilo_data/neo4j/data:/data --env NEO4J_AUTH=neo4j/quneo4j --env NEO4J_dbms_memory_heap_max__size=5G neo4j
    
to reset password remove `neo4j/data/dbms/auth` 

create index over the node's (with Label: `Resource`) name-attribute `CALL db.index.fulltext.createNodeIndex('nodenames', ['Resource'], ['name'])`

* if one has a clean RDF-triple-file: `CALL semantics.liteOntoImport('file:///filename.owl','RDF/XML')`

* count nodes where name endswith `MATCH (n:Resource) WHERE n.name ENDS WITH 'Site>' RETURN COUNT(n)`
* certain uri pathes of length 4 `MATCH p=(x:Resource)-[*4]-() WHERE x.uri='<http://sws.geonames.org/6547429/>' RETURN p LIMIT 25`
* get node by id `MATCH (n:Resource) WHERE Id(n)=8446861 RETURN n`

# some triple-store (rdf dump)
92 files like `output000001.nq.gz`,  `output000092.nq.gz` comprising of 5.5GB  
`find . -type f -name '*.gz' | xargs zcat | wc -l` ->  545_952_516
#### took ~19 hours to populate neo4j with ~500 mio triples
## building a company knowledge-base
1. getting all entities of type "company"  
    `rg -z '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>\t(:?<http://dbpedia.org/ontology/Company>|<http://www.w3.org/ns/org#Organization>)' | gzip > ../companies.txt.gz `

    `zcat ../companies.txt.gz | wc -l` -> 8_055_550
2. extracting company-triples with: `company_knowledge_graph/extract_company_triples_from_raw_dump.py`
  inspecting the triples with `company_knowledge_graph/inspect_triples.py`:  
    * number of company-triples: 84_469_549  
    * number of predictates: 12_906 (see `company_knowledge_graph/company_predicate_counts.json`)
    * `some-path/company_triples$ rg -z 'location.*Berlin'| wc -l` -> 2729
3. building the graph with neo4j:  
    1. `docker run --publish=7474:7474 --publish=7687:7687 --volume=HOME/tilo_data/neo4j/data:/data --env NEO4J_dbms_memory_heap_max__size=5G neo4j`
    2. `python company_knowledge_graph/populate_graph.py` -> takes ~100 sec for 1mio triples
    