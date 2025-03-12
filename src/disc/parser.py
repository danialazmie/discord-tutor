from .map import SCRIPTS, SYMBOLS, GREEK_LETTERS
import re
import matplotlib.pyplot as plt

class MessageChunk:
    def __init__(self, text: str = None, image: str = None):
        self.text = text
        self.image = image

def latex_to_png(expr, fname):
    if not fname.endswith('.png'):
        fname += '.png'

    expr = '$'+expr+'$'
    expr = expr.replace(r'\text', r'\textnormal')
    expr = expr.replace(r'\_', r'_')

    plt.rcParams['text.usetex'] = True
    plt.rcParams['text.latex.preamble'] = r'\usepackage{amsmath}'
    plt.rcParams["figure.figsize"] = (7,1.5)

    plt.text(
        0.5, 
        0.5,  
        expr, 
        size='xx-large', 
        ha='center', 
        c='white'
    )

    plt.axis('off')

    plt.savefig(
        fname=fname, 
        format='png', 
        transparent=True, 
        bbox_inches='tight', 
        pad_inches=0.0, 
        dpi=600
    )
    plt.clf()

    return fname
def replace_scripts(text):
    return re.sub(r"_[0-9aehijklmnoprstuvx]|\^[0-9a-z]", lambda m: SCRIPTS.get(m.group(0), m.group(0)), text)

def get_plaintext(text):
    for i in range(20):
        if len(text) != len(re.sub(r'\$\$([\s\S]*?)\$\$', '', text)):
            text = re.sub(r'\$\$([\s\S]*?)\$\$', '{latex}', text)
            continue
        if len(text) != len(re.sub(r"```([\s\S]*?)```", '', text)):
            text = re.sub(r"```([\s\S]*?)```", '{codeblock}', text)
            continue
        if len(text) != len(re.sub(r"`([^`]+)`", '', text)):
            text = re.sub(r"`([^`]+)`", '{code}', text)
            continue
    return text

def replace_blocks(text, original_text):

    for expr in re.findall(r'\$\$([\s\S]*?)\$\$', original_text):
        text = text.replace('{latex}', f'$${expr}$$', 1)

    for expr in re.findall(r"```([\s\S]*?)```", original_text):
        text = text.replace('{codeblock}', f'```{expr}```', 1)

    if len(original_text) != len(re.sub(r"```([\s\S]*?)```", '', original_text)):
        original_text = re.sub(r"```([\s\S]*?)```", '{codeblock}', original_text)

    for expr in re.findall(r"`([^`]+)`", original_text):
        print('CODE:', expr)
        text = text.replace('{code}', f'`{expr}`', 1)

    return text

def parse_message(text):

    LATEX_FNAME = 'expression'

    fnames = []
    chunks = []

    plaintext = get_plaintext(text)
    plaintext = replace_scripts(plaintext)
    for x, y in GREEK_LETTERS.items():
        plaintext = plaintext.replace(x, y)
    text = replace_blocks(plaintext, text)

    # Chunk using LaTeX

    if '$$' in text:

        indices = [(m.start(0), m.end(0)) for m in re.finditer(r'\$\$([\s\S]*?)\$\$', text)]
        expressions = [text[start:end] for start, end in indices]
        expressions = [substring.strip('\n\t$ ') for substring in expressions]

        for i in range(len(expressions)):
            fnames.append(latex_to_png(expressions[i], f'{LATEX_FNAME}_{i}.png'))

        start = 0

        for i, v in enumerate(indices):

            expr_start = v[0]
            expr_end = v[1]

            chunks.append(MessageChunk(text[start:(expr_end-(expr_end-expr_start))].strip('\n '), fnames[i]))
            start = expr_end

            if i == len(indices)-1:
                chunks.append(MessageChunk(text[expr_end:]))
    else:
        # Need to check for 2000 char limit
        chunks.append(MessageChunk(text))

    final_chunks = []

    while len(chunks) > 0:
        chunk = chunks[0]

        if len(chunk.text) >= 2000:
            if chunk.text[:2000].rfind(r'```python') == -1:
                split_idx = chunk.text[:2000].rfind('\n')
            else:
                split_idx = chunk.text[:2000].rfind(r'```python')

            left = MessageChunk(chunk.text[:split_idx], None)
            chunks[0] = MessageChunk(chunk.text[split_idx:], chunk.image)
            final_chunks.append(left)
        else:
            final_chunks.append(chunk)
            chunks.pop(0)


    return final_chunks
