import logging
import xml.etree.ElementTree as ET

from json import dumps
from typing import NamedTuple, Tuple, Optional
from urllib.parse import urljoin

from .asset import DownloadableFileAsset, aio_download


BASE_URL = 'https://practicetest.icbc.com/'
ASSET_DIR = './assets'

L = logging.getLogger(__name__)


class Question(NamedTuple):
    id_: int
    text: str
    image: Optional[str]
    answer: str
    distractors: Tuple[str, ...]
    chapter: str
    source: str
    link: str

    @property
    def image_asset(self):
        if not self.image:
            return None

        return DownloadableFileAsset(urljoin(BASE_URL, self.image), ASSET_DIR)

    @property
    def anki_image(self):
        if not self.image:
            return ''
        return f'<img src="{self.image_asset.path.parts[-1]}" />'

    def anki_json(self, attr):
        return dumps(getattr(self, attr)).replace('\\', '\\\\').replace("'", "\\'")

    @staticmethod
    def parse_answers(node: ET.Element):
        assert node.tag == 'answers', f'<{node.tag}> is not a <answers> node'

        answer, distractors = None, []
        for n in node.iter():
            if n.tag == 'answer':
                assert answer is None, f'duplicated answer in {node}'
                answer = n.text
            elif n.tag.startswith('distractor_'):
                distractors.append(n.text)
        return answer, distractors

    @staticmethod
    def from_node(node: ET.Element):
        answer, distractors = Question.parse_answers(node.find('answers'))
        image = node.find('image')
        ans = Question(
            id_=int(node.get('id')) + 1,
            text=node.find('text').text,
            image=image.get('file') if image is not None else None,
            answer=answer,
            distractors=distractors,
            chapter=node.find('chapter').text or '',
            source=node.find('source').text or '',
            link=node.find('link').get('src'),
        )

        return ans


def load(filename) -> Tuple[Question]:
    tree = ET.parse(filename)
    root = tree.getroot()
    questions = tuple(Question.from_node(q) for q in root.findall('./questions/question'))
    L.info('%d questions loaded from %s', len(questions), filename)
    return questions


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    questions = load('icbc-practice-questions-english.xml')

    assets = []

    for question in questions:
        L.info('%s - %s', question.id_, question)
        if question.image_asset:
            assets.append(question.image_asset)

    L.info('asset list: %s', assets)
    aio_download(assets)

