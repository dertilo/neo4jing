import os
import sys
from pprint import pprint
from time import time
from typing import List, Tuple

from py2neo import Graph, Node, Relationship
from tqdm import tqdm
from util import data_io, util_methods


def clean_graph(graph: Graph):
    delete_query = (
        "MATCH (n) "
        "WITH n LIMIT 100000 "
        "DETACH DELETE n "
        "RETURN COUNT(*) as return_count"
    )

    # To avoid memory problems, we delete in batches
    num_deleted = 1  # a value lager than 0 to run at least once to the while loop
    c = 0
    while num_deleted > 0:
        num_deleted = graph.run(delete_query).data()[0]["return_count"]
        sys.stdout.write("\r cleaning %d" % c)
        sys.stdout.flush()
        c += 1


class StatefulReader(object):
    def __init__(self, state_file, write_interval=1000_000):
        self.state_file = state_file
        self.write_interval = write_interval

        if os.path.isfile(state_file):
            self.state = data_io.read_json(state_file)
        else:
            self.state = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        data_io.write_json(self.state_file, self.state)
        pprint(self.state)

    def read_lines_from_files(
        self, path, mode="b", encoding="utf-8", limit=sys.maxsize
    ):
        c = 0
        for file in os.listdir(path):
            if self.state.get(file, 0) == "all":
                continue
            for line_idx, line in enumerate(
                data_io.read_lines(path + "/" + file, mode, encoding)
            ):
                c += 1
                if line_idx < self.state.get(file, 0):
                    continue
                if c > limit:
                    break
                yield line
                self.state[file] = line_idx
                if c % self.write_interval == 0:
                    data_io.write_json(self.state_file, self.state)
            self.state[file] = "all"


def fix_spo_order(s, p, o):
    if "resource" in p and "resource" not in s:
        s, p = p, s
    elif "resource" in p and "resource" not in o:
        o, p = p, o
    else:  # <http://dbpedia.org/resource/Piura_Region>      <http://dbpedia.org/property/resources> <http://dbpedia.org/resource/Lemon>
        pass
    return s, p, o


def build_spo_triple(s, p, o):
    s, p, o = fix_spo_order(s, p, o)
    s_name, o_name = s.split("/")[-1], o.split("/")[-1]
    rel_name = p.split("/")[-1]
    spo_triple = {
        "s": s,
        "s_name": s_name,
        "o": o,
        "o_name": o_name,
        "p": p,
        "rel_name": rel_name,
    }
    return spo_triple


if __name__ == "__main__":
    c = 0
    graph = Graph(host="localhost", password="neo4j")
    from pathlib import Path

    home = str(Path.home())

    clean_graph(graph)
    # print('cleaned graph')

    graph.run("CREATE CONSTRAINT ON (resource:Resource) ASSERT resource.uri IS UNIQUE")

    dir = home + "/data/..." #TODO

    # '<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>'
    queues = {"node_prop": [], "spo": []}

    queries = {
        "node_prop": """
            unwind {node_prop} as d
            merge (:Resource {uri: d.s_uri, d.prop_key: d.prop_value })
        """,
        "spo": """
            unwind {spo} as d
            merge (s:Resource {uri: d.s, name: d.s_name })
            merge (o:Resource {uri: d.o, name: d.o_name })
            merge (s)-[:REL {uri:d.p,name:d.rel_name}]->(o)
        """,
    }

    with StatefulReader("./reading_state.jsonl") as reader:
        lines_g = reader.read_lines_from_files(dir)
        tuples_g = (l.split("\t") for l in lines_g)

        batch_size = 10_000
        start = time()
        # line_counter = read_jsons_from_file('.line_counter.json')[0]['num_lines']
        def some_uti_is_too_long(s, p, o):
            return any([len(x) > 200 for x in [s, p, o]])

        tuples_g = (
            (s, p, o) for s, p, o, _ in tuples_g if not some_uti_is_too_long(s, p, o)
        )
        spo_g = (build_spo_triple(s, p, o) for s, p, o in tuples_g)
        # https://stackoverflow.com/questions/26536573/neo4j-how-to-set-label-with-property-value

        def insert_in_neoj4(batch):
            graph.run(queries["spo"], {"spo": batch})

        util_methods.consume_batchwise(insert_in_neoj4, iter(tqdm(spo_g)), batch_size)

'''
542016232it [18:43:20, 8041.72it/s]
'''