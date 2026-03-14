import os
import re

def fix_caps(match):
    text = match.group(0)
    # Ignore small programming brackets
    if text == "[ID]": return "[Id]"
    
    # Capitalize only the first letter of each word
    inner = text[1:-1]
    
    # Title case but keep things like Nsfw? Just title() is fine for now
    # Title will make "URGENTE" -> "Urgente", "ALERTA DE SEGURANÇA" -> "Alerta De Segurança"
    # To be more like "Alerta de segurança", capitalize() is better for sentences, but title() matches the user's request "iniciais das palavras maiusculas"
    
    # Let's use title() but fix small words if needed, or just title()
    res = inner.title()
    return f"[{res}]"

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match brackets containing mainly uppercase and no lowercase
    # \u00C0-\u00DC covers uppercase accented characters in Portuguese
    pattern = re.compile(r'\[[A-Z\u00C0-\u00DC0-9\s\-\(\)\/\_\.]+\]')
    
    new_content = pattern.sub(fix_caps, content)
    
    # Also fix "**[SISTEMA]**" -> "**[Sistema]**"
    # Let's also do a general regex for ALL CAPS words longer than 5 chars outside brackets if they are part of bot messages.
    # Actually the user specifically mentioned "[REINICIALIZAÇÃO QUENTE (HOT-RELOAD)] e todos esse caps lock exaqgerado"
    # I should also replace "CENTRAL DE COMANDOS ZARATHOS" -> "Central De Comandos Zarathos"
    # "COMANDOS DE ADMINISTRAÇÃO" -> "Comandos De Administração"
    
    # Let's replace ANY sequence of uppercase words (3+ chars) if they are 2 or more words
    def fix_all_caps(m):
        if not re.search(r'[a-z]', m.group(0)):
            return m.group(0).title()
        return m.group(0)
        
    pattern2 = re.compile(r'(?<![A-Za-z])([A-Z\u00C0-\u00DC]{3,}(?:\s+[A-Z\u00C0-\u00DC]{2,})+)(?![A-Za-z])')
    new_content = pattern2.sub(fix_all_caps, new_content)
    
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for root, _, files in os.walk('.'):
    for file in files:
        if file.endswith('.py') and file != 'fix_caps.py':
            process_file(os.path.join(root, file))
