from abc import abstractmethod
import requests
import json

from nodes import *

# Base classes for Phapdien Crawler types
class PhapdienCrawlerType:
    def __init__(self):
        pass

class PhapdienCrawler:
    def __init__(self):
        pass

    @abstractmethod
    def get_demuc_content_by_id(self, id):
        pass

    @abstractmethod
    def get_root_nodes(self):
        pass

    @abstractmethod
    def get_children_nodes_by_id(self, id, level):
        pass

class PhapdienCrawlerGetNode(PhapdienCrawlerType):
    def __init__(self, lenmpc=20):
        super().__init__()
        self.type = 'ActionHandler.aspx'
        self.do_type = 'loadnodes'
        self.lenmpc = lenmpc

class PhapdienCrawlerGetTree(PhapdienCrawlerType):
    def __init__(self, lenmpc=20):
        super().__init__()
        self.type = 'TreeBoPD.aspx'
        self.do_type = 'taodanhmucvbkqpd'
        self.lenmpc = lenmpc

class WebPhapDienCrawler(PhapdienCrawler):
    base_url = 'https://phapdien.moj.gov.vn'

    def _transform_raw_phapdien_tree(self, value):
        lines = value.split('\n')
        tree = lines[19]
        raw = tree.split(' \'[{"')
        raw.pop(0)
        result = '[{"' + ''.join(raw)
        result = result[:-3]
        return result

    def get_children_nodes(self, node: PhapdienNode):
        
        lenmpc = 0
        
        if isinstance(node.type, ChuDePhapdienNodeType):
            lenmpc = 0
        elif isinstance(node.type, DeMucPhapdienNodeType):
            lenmpc = 20
        elif isinstance(node.type, ChuongPhapdienNodeType):
            lenmpc = 40
        elif isinstance(node.type, MucPhapdienNodeType):
            lenmpc = 60
        elif isinstance(node.type, DieuPhapdienNodeType):
            lenmpc = 60 + node.type.level * 20
        

        url = f"{self.base_url}/TraCuuPhapDien/ActionHandler.aspx"
        params = {
            'do': 'loadnodes',
            'lenmpc': str(lenmpc)
        }
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://phapdien.moj.gov.vn',
            'Referer': 'https://phapdien.moj.gov.vn/TraCuuPhapDien/MainBoPD.aspx?mapc=',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
        }
        body = {'ItemId': node.id}

        response = requests.post(url, headers=headers, data=body, params=params)

        raw = response.json()
        if raw.get('Erros') != False:
            return []

        raw_data = json.loads(raw['Data'])

        list_children_nodes = []
        for e in raw_data:
            children_node_type = None
            if isinstance(node.type, ChuDePhapdienNodeType):
                children_node_type = DeMucPhapdienNodeType()
            elif isinstance(node.type, DeMucPhapdienNodeType):
                children_node_type = ChuongPhapdienNodeType()
            elif isinstance(node.type, ChuongPhapdienNodeType):
                first_word = e['text'].split(' ')[0].lower().strip()
                children_node_type = MucPhapdienNodeType() if first_word == 'mục' else DieuPhapdienNodeType
            elif isinstance(node.type, MucPhapdienNodeType):
                children_node_type = DieuPhapdienNodeType(level=1)
            elif isinstance(node.type, DieuPhapdienNodeType):
                children_node_type = DieuPhapdienNodeType(level = node.type.level + 1)
            
            list_children_nodes.append(PhapdienNode.from_raw_crawler_data(e, children_node_type))

        return list_children_nodes

    def get_root_nodes(self):
        url = f"{self.base_url}/TraCuuPhapDien/TreeBoPD.aspx"
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }

        response = requests.post(url, headers=headers)
        result = self._transform_raw_phapdien_tree(response.text)
        raw = json.loads(result)

        nodes = []
        for e in raw:
            node = PhapdienNode.from_raw_crawler_data(e, ChuDePhapdienNodeType())
            if node.parent is not None:
                node = node.copy_with(type=DeMucPhapdienNodeType())
            nodes.append(node)
        return nodes

    def get_children_nodes_by_id(self, id, level):
        url = f"{self.base_url}/TraCuuPhapDien/ActionHandler.aspx"
        params = {
            'do': 'loadnodes',
            'lenmpc': str(20 * level)
        }
        headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,vi;q=0.8',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://phapdien.moj.gov.vn',
            'Referer': 'https://phapdien.moj.gov.vn/TraCuuPhapDien/MainBoPD.aspx?mapc=',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
        }
        body = {'ItemId': id}

        response = requests.post(url, headers=headers, data=body, params=params)

        raw = response.json()
        if raw.get('Erros') != False:
            raise Exception(raw)

        raw_data = json.loads(raw['Data'])
        return [
            PhapdienNode.from_raw_crawler_data(e, self._get_node_type_by_level(level, e))
            for e in raw_data
        ]

    def get_demuc_content_by_id(self, id):
        try:
            url = f"{self.base_url}/TraCuuPhapDien/BPD/demuc/{id}.html"
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin'
            }
            response = requests.get(url, headers=headers)
            # This is a hack to fix the encoding issue
            response.encoding = 'utf-8'

            if response.status_code == 200:
                return response.text
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def _get_node_type_by_level(self, level, raw_data):
        # Logic for determining node type by level and content
        if level == 0:
            return DeMucPhapdienNodeType()
        elif level == 1:
            return ChuongPhapdienNodeType()
        elif level == 2:
            first_word = raw_data['text'].split(' ')[0].lower().strip()
            return MucPhapdienNodeType() if first_word == 'mục' else DieuPhapdienNodeType()
        else:
            return DieuPhapdienNodeType({level - 2})

# Example usage:
if __name__ == '__main__':
    crawler = WebPhapDienCrawler()
    root_nodes = crawler.get_root_nodes()
    print(root_nodes)
