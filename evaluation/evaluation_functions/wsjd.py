import os
import subprocess

def compute_wsjd(content):
    
    source_sentences = []
    reference_sentences = []
    hypothesis_sentences = []
    def normalize(text):
        return ' '.join(text.strip().rstrip().replace('\n', ' ').split())
    for ele in content:
        source_sentences.append(normalize(ele['question']))
        reference_sentences.append(normalize(ele['answer']))
        hypothesis_sentences.append(normalize(ele['prediction']))

    with open('temp_sources.txt', 'w') as f1:
        for ele in source_sentences:
            f1.write(f"{ele}\n")
    with open('temp_references.txt', 'w') as f1:
        for ele in reference_sentences:
            f1.write(f"{ele}\n")

    with open('temp_hypothesises.txt', 'w') as f1:
        for ele in hypothesis_sentences:
            f1.write(f"{ele}\n")

    result = subprocess.check_output(
            "python ./utils/compute_gleu.py -r temp_references.txt -s temp_sources.txt -o temp_hypothesises.txt",  # Command to execute the Python file
            shell=True
        )

    os.remove('temp_sources.txt')
    os.remove('temp_references.txt')
    os.remove('temp_hypothesises.txt')

    gleu_score = float(result.decode().strip())
    # print(f"Average GLEU Score: {gleu_score:.4f}")
    return {'score': gleu_score}