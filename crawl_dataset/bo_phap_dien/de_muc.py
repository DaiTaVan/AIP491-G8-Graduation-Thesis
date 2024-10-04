import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from crawler import WebPhapDienCrawler



def _get_demuc_title(raw: str) -> str:
    """Process raw text to extract the 'demuc' title"""
    return ': '.join([s.strip() for s in raw.strip().split('\n') if s.strip()])

def _process_chuong_element(dieu) -> tuple:
    """Process 'chuong' elements"""
    prev = dieu.find_previous_sibling()
    if prev and 'pChuong' in prev.get('class', []):
        chuong_title = prev.get_text().strip() or ''
        prev = prev.find_previous_sibling()
        a_tag = prev.find('a') if prev else None
        chuong_id = a_tag.get('name') if a_tag else ''
        chuong_title = f'{prev.get_text()}: {chuong_title}' if prev else chuong_title
        return (chuong_id, chuong_title)
    return None

def _process_ghi_chu_element(dieu) -> tuple:
    """Process 'ghi chu' (notes) elements"""
    ghi_chu = {
        'itemId': '',
        'locationInVbpl': '',
        'sourceTitle': '',
        'sourceUrl': ''
    }
    sib = dieu.find_next_sibling()
    if sib and 'pGhiChu' in sib.get('class', []):
        a_tag = sib.find('a')
        link = a_tag.get('href') if a_tag else None
        if link:
            link_uri = urlparse(link)
            ghi_chu['itemId'] = parse_qs(link_uri.query).get('ItemID', [''])[0]
            ghi_chu['locationInVbpl'] = link_uri.fragment
        ghi_chu['sourceTitle'] = sib.get_text().strip() or ''
        ghi_chu['sourceUrl'] = link or ''
        sib = sib.find_next_sibling()
    
    return sib, ghi_chu

class VBPLContent:
    def __init__(self, id, title, content, source_title, source_url, item_id, location_in_vbpl, demuc_id, demuc_title, chuong_id, chuong_title):
        self.id = id
        self.title = title
        self.content = content
        self.source_title = source_title
        self.source_url = source_url
        self.item_id = item_id
        self.location_in_vbpl = location_in_vbpl
        self.demuc_id = demuc_id
        self.demuc_title = demuc_title
        self.chuong_id = chuong_id
        self.chuong_title = chuong_title

    def to_json(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'sourceTitle': self.source_title,
            'sourceUrl': self.source_url,
            'itemId': self.item_id,
            'locationInVbpl': self.location_in_vbpl,
            'demucId': self.demuc_id,
            'demucTitle': self.demuc_title,
            'chuongId': self.chuong_id,
            'chuongTitle': self.chuong_title,
        }

    def copy_with(self, **kwargs):
        """Create a copy of VBPLContent with modified fields."""
        return VBPLContent(
            id=kwargs.get('id', self.id),
            title=kwargs.get('title', self.title),
            content=kwargs.get('content', self.content),
            source_title=kwargs.get('source_title', self.source_title),
            source_url=kwargs.get('source_url', self.source_url),
            item_id=kwargs.get('item_id', self.item_id),
            location_in_vbpl=kwargs.get('location_in_vbpl', self.location_in_vbpl),
            demuc_id=kwargs.get('demuc_id', self.demuc_id),
            demuc_title=kwargs.get('demuc_title', self.demuc_title),
            chuong_id=kwargs.get('chuong_id', self.chuong_id),
            chuong_title=kwargs.get('chuong_title', self.chuong_title),
        )

def convert_vbpl_html_to_vbpl_contents(demuc_id: str, raw: str):
    """Convert VBPL HTML content into VBPLContent objects"""
    contents = []
    
    document = BeautifulSoup(raw, 'html.parser')
    
    h3_demuc_title = document.find('h3')
    demuc_title = _get_demuc_title(h3_demuc_title.get_text() if h3_demuc_title else '')

    chuong_element = None
    p_dieus = document.find_all(class_='pDieu')

    for dieu in p_dieus:
        content = VBPLContent(
            id=dieu.find('a')['name'] if dieu.find('a') else '',
            title=dieu.get_text().strip(),
            content='',
            source_title='',
            source_url='',
            item_id='',
            location_in_vbpl='',
            demuc_id=demuc_id,
            demuc_title=demuc_title,
            chuong_id='',
            chuong_title='',
        )

        chuong_element = _process_chuong_element(dieu) or chuong_element
        sib, ghichu_element = _process_ghi_chu_element(dieu)
        content = content.copy_with(
            item_id=ghichu_element['itemId'],
            location_in_vbpl=ghichu_element['locationInVbpl'],
            source_title=ghichu_element['sourceTitle'],
            source_url=ghichu_element['sourceUrl'],
        )

        content_buffer = []
        while sib is not None:
            text = sib.get_text().strip() if sib else ''
            if sib.name == 'table':
                text = table_to_csv(sib)  # You can implement a table to CSV conversion
            content_buffer.append(text)

            sib = sib.find_next_sibling()
            if sib and 'pDieu' in sib.get('class', []):
                break

        content = content.copy_with(
            content='\n'.join(content_buffer).strip(),
            chuong_id=chuong_element[0] if chuong_element else '',
            chuong_title=chuong_element[1] if chuong_element else '',
        )

        contents.append(content)

    return contents

def table_to_csv(table_element):
    """Convert a table HTML element into CSV format (simple implementation)"""
    rows = table_element.find_all('tr')
    csv_data = []
    for row in rows:
        cols = row.find_all(['td', 'th'])
        csv_data.append(','.join([col.get_text().strip() for col in cols]))
    return '\n'.join(csv_data)

if __name__ == '__main__':
    demuc_id = '0cf69ad9-6f29-4ee4-8e16-2c3aa65c3a52'
    raw_content = WebPhapDienCrawler().get_demuc_content_by_id(id=demuc_id)
    contents = convert_vbpl_html_to_vbpl_contents(demuc_id, raw_content)

    # Pretty print the contents as JSON
    print(json.dumps([content.to_json() for content in contents], indent=2, ensure_ascii=False))
