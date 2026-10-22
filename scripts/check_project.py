"""Check first-party skill structure, local links, engine routes and syntax.

Uses the standard library; does not execute game files, tools or Python examples.
"""
from pathlib import Path
from urllib.parse import unquote
import argparse
import ast
import json
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    'GalgameResourceExtract': 'galgame-resource-extract',
    'GalgameTextToSpeech': 'galgame-text-to-speech',
    'GalgameResourcePack': 'galgame-resource-pack',
    'GalgameReverse': 'galgame-reverse',
}


def documents(root):
    return sorted(file for file in root.rglob('*.md')
                  if 'tools' not in file.relative_to(root).parts)


def imported_document(path):
    return 'provenance/entisgls-tools/' in path.as_posix()


def prose(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    text = re.sub(r'`[^`\n]+`', '', text)
    return re.sub(r'https?://[^\s)>]+', '', text)


def destinations(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    text = re.sub(r'`[^`\n]+`', '', text)
    result = re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)', text)
    result += re.findall(r'^\[[^\]\n]+\]:\s*(\S+)', text, flags=re.M)
    result += re.findall(r'\b(?:src|srcset)="([^"]+)"', text)
    return result


def anchors(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    result = set(re.findall(r'\bid=["\x27]([^"\x27]+)["\x27]', text))
    counts = {}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$', text, flags=re.M):
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        number = counts.get(slug, 0)
        result.add(slug if number == 0 else f'{slug}-{number}')
        counts[slug] = number+1
    return result


def check(root):
    root = Path(root).resolve()
    errors, graph, depths = [], {}, []
    docs = documents(root)
    for file in docs:
        text = file.read_text(encoding='utf-8-sig')
        edges = graph.setdefault(file.resolve(), set())
        owner = next((root/s for s in SKILLS if file.is_relative_to(root/s)), root)
        if owner != root and not imported_document(file):
            depth = len(file.relative_to(owner).parts)-1
            depths.append(depth)
            if depth > 1:
                errors.append(f'{file.relative_to(root)}: maintained Markdown must be at most one directory below SKILL.md')
            if file.parent == owner/'engine' and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', file.stem):
                errors.append(f'{file.relative_to(root)}: engine page must use its portable engine name')
        if file.name != 'GLOSSARY.md' and not imported_document(file):
            body = prose(text)
            if re.search(r'(?<![\w/])references/', text):
                errors.append(f'{file.relative_to(root)}: obsolete documentation directory: references/')
            for term in ['原样提取根目录', '原样归档提取根目录', '原样提取目录',
                         '对白配对', '语音配对', '对白出现', '晋升', '回封包', '重封包',
                         '回封装', '重封装', '打包', 'SHA256', '文件校验和']:
                if term in body:
                    errors.append(f'{file.relative_to(root)}: noncanonical term: {term}; see GLOSSARY.md')
        for destination in destinations(text):
            destination = destination.strip().strip('<>')
            if re.match(r'^[a-zA-Z][\w+.-]*:', destination):
                continue
            local, separator, fragment = destination.partition('#')
            target = (file.parent/unquote(local)).resolve() if local else file.resolve()
            if not target.is_relative_to(owner):
                errors.append(f'{file.relative_to(root)}: link leaves standalone skill: {destination}')
            elif not target.exists():
                errors.append(f'{file.relative_to(root)}: missing link: {destination}')
            else:
                edges.add(target)
                if (separator and fragment and target.suffix == '.md'
                        and unquote(fragment) not in anchors(target.read_text(encoding='utf-8-sig'))):
                    errors.append(f'{file.relative_to(root)}: missing heading anchor: {destination}')
        for example in re.findall(r'```python\s*\n(.*?)\n```', text, flags=re.S):
            try:
                ast.parse(example)
            except SyntaxError as error:
                errors.append(f'{file.relative_to(root)}: invalid Python example: {error.msg}')
    python_files = [p for folder in [root/'scripts', root/'tests', *[root/s/'scripts' for s in SKILLS]]
                    for p in folder.glob('*.py')]
    for file in python_files:
        try:
            ast.parse(file.read_text(encoding='utf-8-sig'), filename=str(file))
        except SyntaxError as error:
            errors.append(f'{file.relative_to(root)}:{error.lineno}: {error.msg}')
    for folder, name in SKILLS.items():
        skill = root/folder
        entry = skill/'SKILL.md'
        if not entry.exists():
            errors.append(f'{folder}: missing SKILL.md')
            continue
        text = entry.read_text(encoding='utf-8-sig')
        front = re.match(r'---\n(.*?)\n---\n', text, flags=re.S)
        if (not front or not re.search(r'^name:\s*'+re.escape(name)+r'\s*$', front[1], flags=re.M)
                or not re.search(r'^description:\s*\S', front[1], flags=re.M)):
            errors.append(f'{folder}: invalid skill name or description')
        for file in skill.rglob('*.json'):
            if 'tools' in file.relative_to(skill).parts:
                continue
            try:
                data = json.loads(file.read_text(encoding='utf-8-sig'))
            except (ValueError, UnicodeError) as error:
                errors.append(f'{file.relative_to(root)}: invalid JSON: {error}')
                continue
            if file == skill/'catalog/formats.json':
                ids = set()
                for row in data:
                    target = (skill/row['reference']).resolve()
                    if (row['id'] in ids or row['reference'] != f'engine/{row["id"]}.md'
                            or not target.is_relative_to(skill) or not target.is_file()):
                        errors.append(f'{file.relative_to(root)}: invalid engine route: {row["id"]}')
                    ids.add(row['id'])
                    graph.setdefault(file.resolve(), set()).add(target)
            elif file == skill/'catalog/experiences.json':
                for row in data.get('entries', []):
                    target = (skill/row['reference']).resolve()
                    if (row['reference'] != f'engine/{row["engine"]}.md'
                            or not target.is_relative_to(skill) or not target.is_file()):
                        errors.append(f'{file.relative_to(root)}: invalid learned route')
                    graph.setdefault(file.resolve(), set()).add(target)
        reachable, pending = set(), [entry.resolve(), (skill/'AGENTS.md').resolve()]
        while pending:
            file = pending.pop()
            if file not in reachable:
                reachable.add(file)
                pending.extend(graph.get(file, set())-reachable)
        for file in docs:
            if (file.is_relative_to(skill) and file.name not in {'SKILL.md', 'AGENTS.md'}
                    and not imported_document(file) and file.resolve() not in reachable):
                errors.append(f'{file.relative_to(root)}: unreachable from skill entry or maintenance guide')
            elif (file.is_relative_to(skill) and len(file.relative_to(skill).parts) == 2
                    and file.parent != skill/'engine' and file.resolve() not in graph.get(entry.resolve(), set())):
                errors.append(f'{file.relative_to(root)}: link common guidance directly from SKILL.md')
    for folder in ['GalgameResourceExtract', 'GalgameResourcePack']:
        skill = root/folder
        for pattern in ['tools/GARbro-cli/GARbro.Console.exe', 'tools/ethornell/ethornell.exe',
                        'tools/pfs-rs/pfs-rs.exe', 'tools/cricodecs.exe', 'tools/mangetsu/*.exe']:
            if not list(skill.glob(pattern)):
                errors.append(f'{folder}: missing documented tool: {pattern}')
    helpers = [root/folder/'scripts/engine_experience.py'
               for folder in ['GalgameResourceExtract', 'GalgameResourcePack', 'GalgameReverse']]
    if any(not file.is_file() for file in helpers):
        errors.append('Missing standalone engine experience helper')
    elif len({file.read_bytes() for file in helpers}) != 1:
        errors.append('Standalone experience helpers diverged; update all three copies together')
    return dict(passed=not errors, markdown_files=len(docs), python_files=len(python_files),
                max_document_directory_depth=max(depths, default=0), errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    result = check(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
