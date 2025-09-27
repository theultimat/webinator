#!/usr/bin/env python

import argparse
import markdown
import pathlib
import re

from datetime import datetime


def parse_markdown(path):
    with open(path, 'r') as f:
        lines = [x.strip() for x in f.readlines()]

    # File starts with attribute lines which are of the form @key: value. Parse
    # these until we stop seeing them at which point we should be at the start
    # of the body content.
    attribs = {}
    attrib_pattern = re.compile(r'^@(?P<key>[^:]+):(?P<value>.*)$')

    for i, line in enumerate(lines):
        if not (m := attrib_pattern.match(line)):
            break

        key = m.group('key').strip()
        value = m.group('value').strip()

        if not key.isidentifier() or not key.islower():
            raise Exception(f'Bad key name: "{key}"')

        if key in attribs:
            raise Exception(
                f'Redefinition of attribute "{key}": old="{attribs[key]}" '
                f'new="{value}"'
            )

        attribs[key] = value

    # Add any autogenerate attributes.
    attribs['auto:generated'] = datetime.today().strftime('%Y-%m-%d %H:%M:%S')

    # Now parse the rest of the file as standard markdown.
    body = markdown.markdown(
        '\n'.join(lines[i:]),
        extensions=['footnotes', 'fenced_code'],
    )

    return attribs, body


# Perform a preprocessing pass i.e. include files, evaluate conditionals.
def preprocess(data, attribs):
    changed = False

    # Evaluate all of the conditionals that can be found.
    if_pattern = re.compile(r'\$\$(?P<cond>ifn?):(?P<tag>.*)\{(?P<attrib>[^}]+)\}')
    while m := if_pattern.search(data):
        inv = m.group('cond').strip()[-1] == 'n'
        tag = m.group('tag').strip()
        attrib = m.group('attrib').strip()

        # Find corresponding end pattern.
        end = f'$$end:{tag}{{}}'
        end_idx = data.index(end)

        # Check attribute value and invert if required.
        cond = bool(attribs.get(attrib))
        if inv:
            cond = not cond

        # If condition is true then just remove the condition tags themselves,
        # if not also remove everything between them.
        data = data[:end_idx] + data[end_idx+len(end):]
        if cond:
            data = data[:m.start()] + data[m.end():]
        else:
            data = data[:m.start()] + data[end_idx:]

        changed = True

    # Do a single include update. We don't do multiple at the same time to
    # make sure we catch any conditional includes.
    inc_pattern = re.compile(r'\$\$inc\{(?P<path>[^}]+)\}')
    if m := inc_pattern.search(data):
        with open(m.group('path'), 'r') as f:
            inc_data = f.read()

        data = data[:m.start()] + inc_data + data[m.end():]
        changed = True

    return data, changed


def fill_template(path, attribs, body):
    with open(path, 'r') as f:
        data = f.read()

    # Repeatedly conditionals and includes until nothing is left.
    while True:
        data, changed = preprocess(data, attribs)

        if not changed:
            break

    # Simple find and replace for attributes. These are denoted in the template
    # using $${name}.
    for k, v in attribs.items():
        data = data.replace(f'$${{{k}}}', v)

    # Do the same for body then return.
    return data.replace('$${body}', body)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        'input',
        metavar='INPUT',
        type=pathlib.Path,
        help='Input markdown file to process.',
    )

    parser.add_argument(
        '-o',
        '--output',
        type=pathlib.Path,
        required=True,
        help='Path to output HTML to generate.',
    )

    parser.add_argument(
        '-t',
        '--template',
        type=pathlib.Path,
        required=True,
        help='Path to template file.',
    )

    args = parser.parse_args()

    if not args.input.is_file():
        raise Exception(f'Bad input: {args.inputs}')

    if not args.template.is_file():
        raise Exception(f'Bad template: {args.template}')

    return args


if __name__ == '__main__':
    args = parse_args()
    attribs, body = parse_markdown(args.input)
    html = fill_template(args.template, attribs, body)

    with open(args.output, 'w') as f:
        f.write(html)
