# %%
from typing import List
import json
from tqdm import tqdm
from crawler import WebPhapDienCrawler
from de_muc import convert_vbpl_html_to_vbpl_contents
from nodes import *
# %%
crawler = WebPhapDienCrawler()
root_nodes: List[PhapdienNode] = crawler.get_root_nodes()
[node.to_json() for node in root_nodes]
# %%
chude_nodes = []
all_dieu_nodes = {}
for node in tqdm(root_nodes):
    if isinstance(node.type, ChuDePhapdienNodeType):
        chude_nodes.append(node.to_json())
    elif isinstance(node.type, DeMucPhapdienNodeType):
        demuc_id = node.id
        demuc_content = crawler.get_demuc_content_by_id(id=demuc_id)
        all_dieu_nodes[demuc_id] = [dieu.to_json() for dieu in convert_vbpl_html_to_vbpl_contents(demuc_id=demuc_id,raw=demuc_content)]
# %%
chude_nodes
# %%
all_dieu_nodes
# %%
json.dump([node.to_json() for node in root_nodes], open('/media/tavandai/DATA1/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/root_nodes.json', 'w'))
json.dump(all_dieu_nodes, open('/media/tavandai/DATA1/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/dieu_phap_dien.json', 'w'))
# %%
