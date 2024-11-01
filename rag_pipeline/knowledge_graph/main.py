import json
from schema import *
from neo4j_database import Neo4jDatabase
from tqdm import tqdm

URI = "neo4j://localhost"
AUTH = ("neo4j", "Abc12345")

db = Neo4jDatabase(
        uri=URI, username=AUTH[0], password=AUTH[1]
    )
# db.delete_all_nodes()

db.add_node(BoPhapDienNode())

with open('/media/tavandai/DATA6/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/root_nodes.json') as f1:
    content = json.load(f1)

print("Add root nodes")
for ele in tqdm(content):
    if ele["type"]["type"] == "ChuDePhapdienNodeType":
        node = ChuDePhapdienNode(
            id = ele["id"],
            title = ele["text"]
        )
    if ele["type"]["type"] == "DeMucPhapdienNodeType":
        node = DeMucPhapdienNode(
            id = ele["id"],
            title = ele["text"],
            parent= ele["parent"]
        )
    result = db.add_node(node)
    # print(result)
print("Add relationship of root nodes")
for ele in tqdm(content):
    if ele["type"]["type"] == "ChuDePhapdienNodeType":

        result = db.add_relationship(INSTANCE.BoPhapDien, 'id', "00000000000000000000", 
                            INSTANCE.ChuDePhapdien, 'id', ele["id"],
                            rel_type=Relationship.HAS_SECTION)
        # print(result)
        result = db.add_relationship(INSTANCE.ChuDePhapdien, 'id', ele["id"],
                            INSTANCE.BoPhapDien, 'id', "00000000000000000000", 
                            rel_type=Relationship.BELONGS_TO)
        # print(result)
    if ele["type"]["type"] == "DeMucPhapdienNodeType":

        result = db.add_relationship(INSTANCE.ChuDePhapdien, 'id', ele["parent"], 
                            INSTANCE.DeMucPhapdien, 'id', ele["id"],
                            rel_type=Relationship.HAS_SECTION)
        # print(result)
        result = db.add_relationship(INSTANCE.DeMucPhapdien, 'id', ele["id"],
                            INSTANCE.ChuDePhapdien, 'id', ele["parent"], 
                            rel_type=Relationship.BELONGS_TO)
        # print(result)

with open('/media/tavandai/DATA6/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/dieu_phap_dien.json') as f1:
    content = json.load(f1)

with open('/media/tavandai/DATA6/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/vbpl_title.json') as f1:
    vbpl_title = json.load(f1)

print("Add child nodes")
number_of_demuc = len(list(content.keys()))
for ix, (demuc, listdieu) in enumerate(content.items()):
    print(f"{ix}/{number_of_demuc}")
    # print(demuc)
    for dieu in tqdm(listdieu):
        # print(dieu)
        dieu_node = DieuPhapDienNode(
            id = dieu['id'],
            title = dieu['title'],
            content = dieu['content'],
            parent = dieu['mucID'] if dieu['mucID'] else (dieu['chuongId'] if len(dieu['chuongId']) > 0 else dieu['demucId']),
            parent_type = INSTANCE.MucPhapDien if dieu['mucID'] else (INSTANCE.ChuongPhapDien if len(dieu['chuongId']) > 0 else INSTANCE.DeMucPhapdien),
            references = dieu['contentIDRef'],
            source = json.dumps(SourceDieuPhapDien(
                id = dieu['itemId'],
                url = dieu['sourceUrl'],
                location = dieu['locationInVbpl']
            ).model_dump(), ensure_ascii=False)
        )
        result = db.add_node(dieu_node)
        # print(result)

        original_document_node = TaiLieuPhapLuatGocNode(
            id = dieu['itemId'],
            title = vbpl_title[dieu['itemId']]
        )
        result = db.add_node(original_document_node)
        # print(result)

        if dieu['mucID'] is not None:
            if len(dieu['chuongId']) == 0: 
                raise Exception
            muc_node = MucPhapDienNode(
                id = dieu['mucID'],
                title = dieu['mucTitle'],
                parent = dieu['chuongId'] #if len(dieu['chuongId']) > 0 else  dieu['demucId']
            )
            result = db.add_node(muc_node)
            # print(result)
        if len(dieu['chuongId']) > 0:
            chuong_node = ChuongPhapDienNode(
                id = dieu['chuongId'],
                title = dieu['chuongTitle'],
                parent = dieu['demucId'],
                references = dieu['chuongIDRef']
            )
            result = db.add_node(chuong_node)
            # print(result)

print("Add relationship of child nodes")
number_of_demuc = len(list(content.keys()))
for ix, (demuc, listdieu) in enumerate(content.items()):
    print(f"{ix}/{number_of_demuc}")
    # print(demuc)
    for dieu in tqdm(listdieu):
        # print('-------------------')
        # print(dieu)
        dieu_parent_node_type = INSTANCE.MucPhapDien if dieu['mucID'] else (INSTANCE.ChuongPhapDien if len(dieu['chuongId']) > 0 else INSTANCE.DeMucPhapdien)
        dieu_parent_id = dieu['mucID'] if dieu['mucID'] else (dieu['chuongId'] if len(dieu['chuongId']) > 0 else dieu['demucId'])
        result = db.add_relationship(dieu_parent_node_type, 'id', dieu_parent_id, 
                                    INSTANCE.DieuPhapDien, 'id', dieu["id"],
                                    rel_type=Relationship.HAS_SECTION)
        # print(result)

        result = db.add_relationship(INSTANCE.DieuPhapDien, 'id', dieu["id"],
                                    dieu_parent_node_type, 'id', dieu_parent_id, 
                                    rel_type=Relationship.BELONGS_TO)
        # print(result)

        for dieu_ref_id in dieu['contentIDRef']:
            result = db.add_relationship(INSTANCE.DieuPhapDien, 'id', dieu["id"],
                                    INSTANCE.DieuPhapDien, 'id', dieu_ref_id, 
                                    rel_type=Relationship.RELATE_TO, raise_exception=False)
            # print(result)
        
        result = db.add_relationship(INSTANCE.DieuPhapDien, 'id', dieu["id"], 
                                    INSTANCE.TaiLieuPhapLuatGoc, 'id', dieu['itemId'],
                                    rel_type=Relationship.DERIVED_FROM, 
                                    rel_properties={"location": dieu['locationInVbpl']})
        # print(result)

        result = db.add_relationship(INSTANCE.TaiLieuPhapLuatGoc, 'id', dieu['itemId'],
                                    INSTANCE.DieuPhapDien, 'id', dieu["id"],
                                    rel_type=Relationship.SOURCE_OF,
                                    rel_properties={"location": dieu['locationInVbpl']})
        # print(result)

        if dieu['mucID'] is not None:
            if len(dieu['chuongId']) == 0: 
                raise Exception
            result = db.add_relationship(INSTANCE.MucPhapDien, 'id', dieu['mucID'],
                                    INSTANCE.ChuongPhapDien, 'id', dieu['chuongId'],
                                    rel_type=Relationship.BELONGS_TO)
            # print(result)

            result = db.add_relationship(INSTANCE.ChuongPhapDien, 'id', dieu['chuongId'],
                                    INSTANCE.MucPhapDien, 'id', dieu['mucID'],
                                    rel_type=Relationship.HAS_SECTION)
            # print(result)
        if len(dieu['chuongId']) > 0:
            result = db.add_relationship(INSTANCE.ChuongPhapDien, 'id', dieu['chuongId'],
                                    INSTANCE.DeMucPhapdien, 'id', dieu['demucId'],
                                    rel_type=Relationship.BELONGS_TO)
            # print(result)

            result = db.add_relationship(INSTANCE.DeMucPhapdien, 'id', dieu['demucId'],
                                    INSTANCE.ChuongPhapDien, 'id', dieu['chuongId'],
                                    rel_type=Relationship.HAS_SECTION)
            # print(result)
