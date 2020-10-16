import logging

import genanki

from . import datasource


L = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

static_files = {
    'qfmt': './static/front.html',
    'afmt': './static/back.html',
    'styles': './static/styles.css',
}

static_contents = {}

for k, filename in static_files.items():
    L.info('load static file %s to %s', filename, k)
    with open(filename, 'r', encoding='utf-8') as f:
        static_contents[k] = f.read()

L.info(static_contents)

my_model = genanki.Model(
    0x3e710001,
    'ICBC Test Model',
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


def load_deck(deck: genanki.Deck, source: str, sort_id_base: int):
    questions = datasource.load(source)
    assets = [question.image_asset for question in questions if question.image_asset]

    for question in questions:
        note = genanki.Note(
            model=my_model,
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
    return assets

rule_deck = genanki.Deck(
    0x3e720001,
    'ICBC Practice Test'
)
sign_deck = genanki.Deck(
    0x3e720002,
    'ICBC Practice Test (Signs)'
)

assets = []
assets += load_deck(rule_deck, 'icbc-practice-questions-english.xml', 0)
assets += load_deck(sign_deck, 'icbc-practice-questions-english-signs.xml', 1000)
datasource.aio_download(assets)

deck = genanki.Package([rule_deck, sign_deck])
deck.media_files = [asset.path for asset in assets]
deck.write_to_file('icbc-practice-test.apkg')
L.info('deck generated.')

