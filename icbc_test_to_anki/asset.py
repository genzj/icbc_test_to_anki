import asyncio
import io
import logging

from urllib.parse import urlparse, ParseResult
from typing import NamedTuple, Union, Optional, List
from mimetypes import guess_type
from pathlib import Path

from aiohttp_requests import requests


L = logging.getLogger(__name__)

class FileAsset:
    path: Path
    mime: str

    def __init__(self, path: Union[str, Path], mime: str):
        path = Path(path)
        self.path = path
        self.mime = mime

    @staticmethod
    def in_dir(base_dir: Union[str, Path], filename: Union[str, Path], mime: str, create_base_dir=True):
        base_dir = Path(base_dir)
        filename = Path(filename)

        if create_base_dir:
            base_dir.mkdir(exist_ok=True)

        assert base_dir.is_dir(), f'{base_dir} is not a directory'

        return FileAsset(
            path=Path(base_dir) / Path(filename),
            mime=mime
        )

    def exists(self):
        return self.path.exists()

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.path}>'


class DownloadableFileAsset:
    local: FileAsset
    url: str

    def __init__(self, url: str, local_dir: Union[str, Path], filename: Union[str, Path, None]=None, mime: Optional[str]=None):
        if not filename:
            parsed = urlparse(url)
            L.debug('parsed %s', parsed)
            filename = Path(parsed.path).parts[-1]
            L.debug('filename %s', filename)

        if not mime:
            mime = guess_type(url)[0]

        assert bool(mime), f'mime cannot be guessed from URL, specify it explicitly'

        self.url = url
        self.local = FileAsset.in_dir(local_dir, filename, mime, True)

    @property
    def path(self) -> Path:
        return self.local.path

    async def download(self, force=False):
        if not force and self.local.exists():
            L.info('%s exists, ignore url %s', self.path, self.url)
            return

        response = await requests.get(self.url)
        if response.status != 200:
            msg = f'download {self.url} failed: {response.reason}'
            L.error(msg)
            raise Exception(msg)

        with open(self.path, 'wb') as f:
            f.write(await response.read())
        L.info('%s saved to %s', self.url, self.local)

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.url} -> {self.path}>'

async def download_many(assets: List[DownloadableFileAsset], force: bool=False):
    return await asyncio.wait(
        {asset.download(force=force) for asset in assets},
        return_when=asyncio.ALL_COMPLETED,
    )


def aio_download(assets: List[DownloadableFileAsset], force: bool=False):
    loop = asyncio.new_event_loop()
    done, pending = loop.run_until_complete(download_many(assets, force=force))

    L.info('%d/%d items downloaded', len(done), len(assets))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    a1 = DownloadableFileAsset(
        'https://practicetest.icbc.com/images/opkt/q156.png', './assets'
    )
    a2 = DownloadableFileAsset(
        'https://practicetest.icbc.com/images/opkt/q11.png', './assets'
    )
    a3 = DownloadableFileAsset(
        'https://practicetest.icbc.com/images/opkt/q8.png', './assets'
    )
    a4 = DownloadableFileAsset(
        'https://practicetest.icbc.com/images/opkt/q1.png', './assets'
    )

    aio_download([a1, a2, a3, a4])

