from functools import partial

from py2neo import Graph, Node, Relationship

def clean_graph(graph: Graph):
    delete_query = 'MATCH (n) ' \
                   'WITH n LIMIT 1000 ' \
                   'DETACH DELETE n ' \
                   'RETURN COUNT(*) as return_count'

    # To avoid memory problems, we delete in batches
    return_count = 1  # a value lager than 0 to run at least once to the while loop

    while return_count > 0:
        return_count = graph.run(delete_query).data()[0]['return_count']

def add_to_subgraph(entity,subgraph):
    subgraph[0] = subgraph[0]|entity
    return entity

PARTICIPATES = 'participates'
INTERACTION = 'interaction'
PROTEIN = 'protein'

if __name__ == '__main__':
    graph = Graph(password='scisci')
    clean_graph(graph)

    tx = graph.begin()
    akap = Node(*[PROTEIN], **{'name': 'AKAP', 'full_name': 'A-kinase anchoring protein (AKAP)'})
    camp = Node('signaling pathways',name='cAMP', full_name='cyclic adenosine monophosphate (cAMP)')
    subgraphs = [akap | camp]
    add = partial(add_to_subgraph,subgraph=subgraphs)
    pka = add(Node(PROTEIN, full_name='kinase A (PKA)', name='PKA'))
    pka_dependent_to_camp = add(Relationship(pka, 'dependent_to', camp))

    # akap_pka_rel = add(Relationship(akap, INTERACTION, pka))
    phd = add(Node('project', name='phd', full_name='proposed PhD project'))
    akap_pka_interaction = add(Node(INTERACTION, name='a interacts with b'))
    add(Relationship(akap, 'a', akap_pka_interaction))
    add(Relationship(akap_pka_interaction, 'b', pka))


    phd_stuff = add(Relationship(phd,'validate',akap_pka_interaction))

    fmp_api_1 = add(Node('small molecule', name='FMP-API-1'))
    # 'both in vitro and in cultured cardiac myocytes, by binding to an allosteric site of the regulatory PKA subunit'
    add(Relationship(fmp_api_1, 'inhibits', akap_pka_interaction))
    add(Relationship(fmp_api_1,'activates',pka))
    sm = add(Node('small molecule', name='NoNameSM'))

    akap_lbc = add(Node(PROTEIN, name='AKAP-Lbc'))
    rhoa = add(Node(PROTEIN, name='RhoA'))

    interaction_akaplbc_rhoa = add(Node(INTERACTION, name='a interacts with b'))
    add(Relationship(akap_lbc,'a',interaction_akaplbc_rhoa))
    add(Relationship(interaction_akaplbc_rhoa,'b',rhoa))

    # add(Relationship(sm,'disrupts',interaction_akaplbc_rhoa))
    sm_dis_i = add(Node('disrupted',name='1. disrupts 2.'))
    add(Relationship(sm,'1',sm_dis_i))
    add(Relationship(sm_dis_i,'2',interaction_akaplbc_rhoa))

    suessmuth_group = add(Node('group',name='Süssmuth group at the TU Berlin'))
    add(Relationship(suessmuth_group,'identified',sm))

    aqp2 = add(Node('water channel',name='AQP2',full_name='aquaporin-2'))
    avp = add(Node('unknown',name='AVP'))
    plasma_mem = add(Node('unknown',name='plasma membrane'))

    promotion_of_redistr_of_aqp2_by_sm = add(Node('promote redistribution',name='1 prom. the redistr. of 2 to 3'))

    add(Relationship(sm,'1',promotion_of_redistr_of_aqp2_by_sm))
    add(Relationship(promotion_of_redistr_of_aqp2_by_sm,'2',aqp2))
    add(Relationship(promotion_of_redistr_of_aqp2_by_sm,'3',plasma_mem))
    add(Relationship(promotion_of_redistr_of_aqp2_by_sm,'independent_of',avp))

    add(Relationship(sm_dis_i,'enables',promotion_of_redistr_of_aqp2_by_sm))

    subgraph = subgraphs[0]
    print(subgraph._Subgraph__nodes)
    tx.create(subgraph)
    tx.commit()
