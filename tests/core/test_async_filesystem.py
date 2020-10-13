import pytest
import os
import shutil
import aiofiles
import aiofiles.os

from core import async_filesystem

pytestmark = pytest.mark.asyncio

#
# @pytest.mark.parametrize('fs, date, url', [('fs', '2020-01-01', 'a' * 255)])
# def test__encode_filepath(fs, date, url, tmp_path):
#     d = tmp_path / 'fs/20200101/'
#     d.mkdir(parents=True, exist_ok=True)
#     file_path = async_filesystem._encode_filepath(fs, date, url)
#     assert len(file_path) == 255
#     assert file_path.count('a') == 255 - 17
#     shutil.rmtree(fs)
#
#
# @pytest.mark.parametrize('url', ['MYURL.COM/EXAMPLE'])
# def test__decode_filepath(url):
#     decoded_file_path = async_filesystem._decode_filepath(url)
#     assert decoded_file_path == 'myurl.comIexample.html'
#
#
# def test_create_fs(tmp_path):
#     async_filesystem.create_fs(str(tmp_path))
#     assert os.path.isdir(str(tmp_path))
#
#
# @pytest.mark.parametrize('fs, date, url, use_glob', [('fs', '2020-01-01', 'bbbb' + 'a' * 255, True),
#                                                      ('fs', '2020-01-01', 'bbbb' + 'a' * 255, False),
#                                                      ])
# def test_exists_file(fs, date, url, use_glob):
#     file_path = async_filesystem._encode_filepath(fs, date, url)
#     os.makedirs(file_path.rsplit('/', 1)[0], exist_ok=True)
#     with open(file_path, 'w') as f:
#         f.write('')
#     if use_glob:
#         # glob will only show max 255 chars TOTAL, whereas find is showing 255 chars per file/dir. glob trims the end
#         # of the file excluding the extension
#         assert not async_filesystem.exists_file(fs, url, use_glob)
#     else:
#         assert async_filesystem.exists_file(fs, url, use_glob)
#     shutil.rmtree(fs)
#
#
# @pytest.mark.parametrize('fs, date, url', [('fs', '20200101', 'https://www.example.com'),
#                                            ('fs', '20200101', '')
#                                            ])
# async def test_get_filepath(fs, date, url):
#     file_path = async_filesystem._encode_filepath(fs, date, url)
#     aiofiles.os.wrap(os.makedirs(f"{fs}/{date}/", exist_ok=True))
#     async with aiofiles.open(file_path, 'w') as f:
#         await f.write('')
#     out = async_filesystem.get_filepath(fs, url)
#     assert out
#     shutil.rmtree(fs)
#
#
# def test_load_file():
#     # assert False
#     pass


@pytest.mark.parametrize('fs, html, encoding',
                         [('fs', '<html></html>', None),
                          ('fs', '<html></html>', 'latin-1'),
                          ('fs', b'<html></html>', 'latin-1'),
                          ])
async def test_save_file(fs, html, encoding, afs):
    file_path = await async_filesystem.save_file(fs, html, encoding)
    # file_path = async_filesystem._encode_filepath(fs, date, url)
    assert file_path and afs.exists(file_path)
    await aiofiles.os.wrap(os.remove)(file_path)


# def test_search_fs():
#     # assert False
#     pass
