import logging

import genanki

from typing import List
from . import datasource


L = logging.getLogger(__name__)


static_files = {
    'qfmt': './static/front.html',
    'afmt': './static/back.html',
    'styles': './static/styles.css',
}


_static_contents = {}

def get_static_contents():
    global _static_contents

    if not _static_contents:
        for k, filename in static_files.items():
            L.info('load static file %s to %s', filename, k)
            with open(filename, 'r', encoding='utf-8') as f:
                _static_contents[k] = f.read()

        L.debug('static files lodaed:', _static_contents)
    return _static_contents


def create_model(model_id: int, model_name: str):
    static_contents = get_static_contents()
    return genanki.Model(
        model_id,
        model_name,
        fields=[
            {'name': 'ID'},
            {'name': 'Question'},
            {'name': 'Image'},
            {'name': 'Answer'},
            {'name': 'Choices'},
            {'name': 'Chapter'},
            {'name': 'Source'},
        ],
        css=static_contents['styles'],
        templates=[
        {
            'name': 'ICBC Practice Test',
            'qfmt': static_contents['qfmt'],
            'afmt': static_contents['afmt'],
        },
    ])


def load_deck(deck: genanki.Deck, model: genanki.Model, assets: List, source: str, sort_id_base: int):
    questions = datasource.load(source)
    assets += [question.image_asset for question in questions if question.image_asset]

    for question in questions:
        note = genanki.Note(
            model=model,
            fields=[
                '%04d' % (question.id_ + sort_id_base,),
                f'{question.id_}. {question.text}',
                question.anki_image,
                question.anki_json('answer'),
                question.anki_json('distractors'),
                question.chapter,
                question.source,
            ]
        )

        deck.add_note(note)


def main():
    rule_model = create_model(
        0x3e710001,
        'ICBC Rule Test Model'
    )
    rule_deck = genanki.Deck(
        0x3e720001,
        'ICBC Rule Test'
    )


    # Anki Android requires unique model for each deck
    sign_model = create_model(
        0x3e710002,
        'ICBC Sign Test Model'
    )
    sign_deck = genanki.Deck(
        0x3e720002,
        'ICBC Sign Test'
    )

    assets = []
    load_deck(rule_deck, rule_model, assets, 'icbc-practice-questions-english.xml', 0)
    load_deck(sign_deck, sign_model, assets, 'icbc-practice-questions-english-signs.xml', 1000)
    datasource.aio_download(assets)

    deck = genanki.Package([rule_deck, sign_deck])
    deck.media_files = [asset.path for asset in assets]
    deck.write_to_file('icbc-practice-test.apkg')
    L.info('deck generated.')

