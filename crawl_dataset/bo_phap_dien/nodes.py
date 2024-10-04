import json
from bs4 import BeautifulSoup

class PhapdienNodeType:
    def __init__(self):
        pass

    @staticmethod
    def from_json(data):
        if isinstance(data, dict):
            node_type = data.get('type')
            if node_type == 'ChuDePhapdienNodeType':
                return ChuDePhapdienNodeType()
            elif node_type == 'DeMucPhapdienNodeType':
                return DeMucPhapdienNodeType()
            elif node_type == 'ChuongPhapdienNodeType':
                return ChuongPhapdienNodeType()
            elif node_type == 'DieuPhapdienNodeType':
                return DieuPhapdienNodeType(data.get('level'))
        raise ValueError("Invalid PhapdienNodeType")

    @staticmethod
    def to_json(node_type):
        if isinstance(node_type, ChuDePhapdienNodeType):
            return {'type': 'ChuDePhapdienNodeType'}
        elif isinstance(node_type, DeMucPhapdienNodeType):
            return {'type': 'DeMucPhapdienNodeType'}
        elif isinstance(node_type, ChuongPhapdienNodeType):
            return {'type': 'ChuongPhapdienNodeType'}
        elif isinstance(node_type, MucPhapdienNodeType):
            return {'type': 'MucPhapdienNodeType'}
        elif isinstance(node_type, DieuPhapdienNodeType):
            return {'type': 'DieuPhapdienNodeType', 'level': node_type.level}
        raise ValueError("Unknown PhapdienNodeType")


class ChuDePhapdienNodeType(PhapdienNodeType):
    def __init__(self):
        super().__init__()


class DeMucPhapdienNodeType(PhapdienNodeType):
    def __init__(self):
        super().__init__()


class ChuongPhapdienNodeType(PhapdienNodeType):
    def __init__(self):
        super().__init__()


class MucPhapdienNodeType(PhapdienNodeType):
    def __init__(self):
        super().__init__()


class DieuPhapdienNodeType(PhapdienNodeType):
    def __init__(self, level):
        super().__init__()
        self.level = level


class PhapdienNode:
    def __init__(self, id, parent, text, can_open_detail, can_open_category, type):
        self.id = id
        self.parent = parent
        self.text = text
        self.can_open_detail = can_open_detail
        self.can_open_category = can_open_category
        self.type = type

    @staticmethod
    def from_raw_crawler_data(data, type: PhapdienNodeType):
        can_open_detail = False
        can_open_category = False
        text = ''
        parent = data.get('parent', None)

        if parent == '#' or parent is None:
            parent = None
        elif not isinstance(parent, str):
            parent = None

        # Parsing the HTML content using BeautifulSoup
        element = BeautifulSoup(data.get('text', ''), 'html.parser')
        elements = element.find_all('a')

        for link in elements:
            link_text = link.text
            if link_text == '(Xem chi tiết)':
                can_open_detail = True
            elif link_text == '(Xem danh mục văn bản)':
                can_open_category = True
            link.extract()  # Remove the element from the DOM

        # Get the remaining text
        text = element.get_text().strip()

        return PhapdienNode(
            id=data.get('id', ''),
            parent=parent,
            text=text,
            type=type,
            can_open_detail=can_open_detail,
            can_open_category=can_open_category
        )

    @staticmethod
    def from_json(json_data):
        return PhapdienNode(
            id=json_data['id'],
            parent=json_data.get('parent'),
            text=json_data['text'],
            can_open_detail=json_data['canOpenDetail'],
            can_open_category=json_data['canOpenCategory'],
            type=PhapdienNodeType.from_json(json_data['type'])
        )

    def to_json(self):
        return {
            'id': self.id,
            'parent': self.parent,
            'text': self.text,
            'canOpenDetail': self.can_open_detail,
            'canOpenCategory': self.can_open_category,
            'type': PhapdienNodeType.to_json(self.type)
        }

    def copy_with(self, **kwargs):
        """Implements copy_with functionality manually"""
        return PhapdienNode(
            id=kwargs.get('id', self.id),
            parent=kwargs.get('parent', self.parent),
            text=kwargs.get('text', self.text),
            can_open_detail=kwargs.get('can_open_detail', self.can_open_detail),
            can_open_category=kwargs.get('can_open_category', self.can_open_category),
            type=kwargs.get('type', self.type)
        )


# Extension for list of PhapdienNode objects to JSON conversion
def phapdien_node_list_to_json(node_list):
    return [node.to_json() for node in node_list]

