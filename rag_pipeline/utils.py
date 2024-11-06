from typing import Dict
from vector_database import Node

def node_to_dictionary(node: Node):
    dict_result = {
        'id': node["id"],
        'dense_vector': node["dense_vector"],
        'sparse_vector': node["sparse_vector"],
        'metadata': node["metadata"]
    }

    return dict_result

def dictionary_to_node(dict_input: Dict):
    return Node(
        id = dict_input['id'],
        dense_vector = dict_input['dense_vector'],
        sparse_vector = dict_input['sparse_vector'],
        metadata = dict_input['metadata']
    )