import json
from parser import parse_law, SentenceSplitter
from transformers import AutoTokenizer
from parser import SentenceSplitter
from tqdm import tqdm
from uuid import uuid4

with open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/dieu_phap_dien_fix.json') as f1:
    all_dieu = json.load(f1)

with open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/dataset/Phapdien/vbpl_title.json') as f1:
    titles = json.load(f1)



tokenizer = AutoTokenizer.from_pretrained('bge-m3')
parser = SentenceSplitter(tokenizer=tokenizer, chunk_size=256)

max_tokens = 0
all_contents = {}
all_contents_mapping = {}
for c, (ix, values) in enumerate(all_dieu.items()):
    print(c,'/', len(list(all_dieu.keys())))

    for ixs, value in tqdm(enumerate(values)):
        all_contents[value['id']] = []

        dieu_index = value['locationInVbpl'].split('_')[-1]
        dieu_title = ' '.join(value['title'].split(' ')[2:])
        dieu_content = value['content'].replace("\xa0", " ").strip()
        dieu_all_content = f"Điều {dieu_index}. {dieu_title}\n{dieu_content}"

        parsed_law = list(parse_law(dieu_all_content).values())[0]

        source_title = value['sourceTitle'][1:-1]
        vbpl_goc_title = titles[value['itemId']]
        ref_dieu = vbpl_goc_title if len(vbpl_goc_title) > 0 else source_title

        sub_elements = []
        if len(list(parsed_law['sections'])) == 0:
            sub_elements.extend(
                            parser.split(title=f"{ref_dieu}\n{parsed_law['title']}\n" + parsed_law['content'].split('\n')[0], content='\n'.join(parsed_law['content'].split('\n')[1:]))
                        )
        else:
            if len(tokenizer.convert_tokens_to_ids(tokenizer.tokenize(parsed_law['content']))) > 512:
                text_combine =  '\n'.join(parsed_law['content'].split('\n')[1:]) + '\n'
                for _, khoan_dict in parsed_law['sections'].items():
                    text_combine += khoan_dict['content'] + '\n' + '\n'.join(khoan_dict['subsections'])
                                              
                sub_elements.extend(
                                parser.split(title=f"{ref_dieu}\n{parsed_law['title']}\n" + parsed_law['content'].split('\n')[0], content=text_combine)
                            )
            else:
                for _, khoan_dict in parsed_law['sections'].items():
                    if len(khoan_dict['subsections']) == 0:
                        sub_elements.extend(
                                parser.split(title=f"{ref_dieu}\n{parsed_law['title']}\n{parsed_law['content']}\n" + khoan_dict['content'].split('\n')[0], content='\n'.join(khoan_dict['content'].split('\n')[1:]))
                            )
                    else:
                        if len(tokenizer.convert_tokens_to_ids(tokenizer.tokenize(khoan_dict['content']))) < 512:
                            for sub_section in khoan_dict['subsections']:
                                
                                    sub_elements.extend(
                                        parser.split(title=f"{ref_dieu}\n{parsed_law['title']}\n{parsed_law['content']}\n{khoan_dict['content']}", content=sub_section)
                                    )
                        else:
                            sub_elements.extend(
                                parser.split(title=f"{ref_dieu}\n{parsed_law['title']}\n{parsed_law['content']}\n" + khoan_dict['content'].split('\n')[0], content='\n'.join(khoan_dict['content'].split('\n')[1:]+khoan_dict['subsections']))
                            )
        
        for element in sub_elements:
            gen_id = str(uuid4())
            all_contents_mapping[gen_id] = element
            all_contents[value['id']].append(gen_id)

json.dump(all_contents, open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/all_contents.json', 'w'), indent=2, ensure_ascii=False)
json.dump(all_contents_mapping, open('/media/tavandai/DATA23/fpt_university/Graduation_Thesis/AIP491-G8-Graduation-Thesis/rag_pipeline/data_v2/all_contents_mapping.json', 'w'), indent=2, ensure_ascii=False)
                