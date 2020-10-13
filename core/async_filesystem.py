"""
Linux-based File System for saving/searching/loading files
"""

import os
import re
import subprocess
import glob
from core import async_write, logger
from typing import Union, Optional, ByteString

basiclogger = logger.rabbit_logger(__name__)


# def _encode_filepath(fs: str, date: str, url: str):
#     """
#     Encodes file path and makes dirs for the filesystem with FS:/date/url
#
#     Args:
#         fs (str): Top of the filesystem directory, path or directory name
#         date (str): string. date in YYYY-MM-DD (with or without delimiter is fine)
#         url (str): url string to be encoded
#
#     Returns:
#         Encoded file_path
#
#
#     .. todo:: handle .asp and .aspx webpage where end result could be url/url/url.aspx.html
#
#     """
#
#     folder = re.sub('\W+', '', date)[:8]
#     path = f'{fs}/{folder}/'
#     create_fs(path)
#
#     file_path = path + url.lower().replace('/', 'I')
#     file_path = file_path[:min(250, len(file_path))]
#
#     # TODO  handle .asp and .aspx webpage where end result could be url/url/url.aspx.html
#     if not file_path.endswith('.html') and not file_path.endswith('.htm'):
#         file_path += '.html'
#     return file_path


# def _decode_filepath(url: str):
#     """
#     Decodes a url by:
#         1. Lowering all chars in the string
#         2. replacing all '/' with 'I'
#         3. picks the min(250 chars, length of url string)
#         4. appending .html to any url that does not end with .html or htm
#
#     Args:
#         url (str):
#
#     Returns:
#         decoded url string
#     """
#     html = url.lower().replace('/', 'I')
#     html = html[:min(250, len(html))]
#     if not html.endswith('.html') and not html.endswith('.htm'):
#         html += '.html'
#     return html


def create_fs(fs: str):
    """
    Creates a File System directory. If the directory already exists, it does not overwrite the contents.

    Args:
        fs (str): path or directory name

    Returns:
        None
    """

    os.makedirs(fs, exist_ok=True)


# def exists_file(fs: str, url: str, use_glob: bool = False):
#     """
#     Checks if a url is already saved to the filesystem and returns True or False
#
#     Args:
#         fs (str): Top of the filesystem directory, path or directory name
#         url (str): url str to check in the filesystem. It is decoded using _decode_filepath(url)
#         use_glob (bool): whether to use `glob` (True) instead of linux `find`. Default False
#
#     Returns:
#         True or False if url exists in the filesystem
#     """
#     if not url:
#         # case of passing empty string as url,
#         return False
#     # print(url)
#     url = _decode_filepath(url)
#
#     if not use_glob:
#         proc = subprocess.Popen(['/usr/bin/find', f'{fs}/*/{url}'], stdout=subprocess.PIPE,
#                                 stderr=subprocess.DEVNULL, shell=True)
#         (out, err) = proc.communicate()
#
#         if out == b'':
#             return False
#         return True
#     else:
#         out = glob.glob(f'{fs}/*/{url}')
#         if out:
#             return True
#         # print('ALREADY EXISTS',out)
#         return False


# def get_filepath(fs: str, url: str) -> Union[str, bytes]:
#     """
#     Decodes the url, and opens up a subprocess to run find on the url in the filesystem under fs/\*/decoded_url
#     Args:
#         fs (str): Top of the filesystem directory, path or directory name
#         url (str): url str to check in the filesystem. It is decoded using _decode_filepath(url)
#
#     Returns:
#         File path if found, else None
#
#     """
#     url = _decode_filepath(url)
#     # check the path to the find function, sometimes its /bin/find
#     proc = subprocess.Popen('/usr/bin/find ' + fs + '/*/' + url + ' 2>/dev/null', stdout=subprocess.PIPE, shell=True)
#     (out, err) = proc.communicate()
#     return out


# def load_file(fs: str, url: str):
#     """
#     `cats` a file from filesystem using /bin/cat
#
#     Args:
#         fs (str): Top of the filesystem directory, path or directory name
#         url (str): url str to check in the filesystem. It is decoded using _decode_filepath(url)
#
#     Returns:
#         text of file if found.
#
#     """
#     url = _decode_filepath(url)
#     proc = subprocess.Popen('/bin/cat ' + fs + '/*/' + url + ' 2>/dev/null', stdout=subprocess.PIPE, shell=True)
#     (out, err) = proc.communicate()
#     return out


async def save_file(fpath: str, html: Union[str, ByteString], encoding: Optional[str] = None) -> \
        Union[bool, str]:
    """
    Encodes the filepath and saves the html using async_write

    Args:
        fpath (str): Top of the filesystem directory, path or directory name
        date (str): date in YYYY-MM-DD (with or without delimiter is fine). Directory will be created one level down
        from fs
        url (str): url str to check in the filesystem. It is decoded using _decode_filepath(url)
        html (str or bytes): html response string to be written
        encoding (str):

    Returns:
        path string if written, and False if Exception was raised.
    """

    # path = _encode_filepath(fs, date, url)
    try:
        if isinstance(html, str):
            save_type = 'w'
        else:
            save_type = 'wb'
        await async_write.write_data(fpath, html, save_type, encoding)
    except Exception as exc:
        basiclogger.error(f"{fpath}, {exc.__repr__()}")
        return False
    return fpath


# def search_fs(fs: str, query: str):
#     """
#     Performs a linux 'grep' using a query on the filesystem
#
#     Args:
#         fs (str): Top of the filesystem directory, path or directory name
#         query (str): string like grep query
#
#     Returns:
#         results of grep query
#
#
#     .. todo:: todo line below needs to be generalized for LOB, etc.
#
#     """
#     proc = subprocess.Popen('/bin/grep -s -R -i "' + query + '" ' + fs + '/*', stdout=subprocess.PIPE, shell=True)
#     (out, err) = proc.communicate()
#     A = {}
#     for record in str(out).strip().split('\\n')[:-1]:
#         fields = record.split('|')
#         url = fields[0]
#         if url.startswith('b"'):
#             url = url[2:]
#         if url.startswith('b\''):
#             url = url[2:]
#         url = ':'.join(url.split(':')[:-1])
#         # todo line below needs to be generalized for LOB, etc.
#         url = url.replace('sentiment/', 'pages/')
#         info = fields[1:]
#         if not url in A:  # if test for membership, then this should be if url not in A
#             A[url] = []
#         A[url].append(info)
#
#     results = []
#     for url in A:
#         for rec in A[url]:
#             results.append([url] + rec)
#     return results
