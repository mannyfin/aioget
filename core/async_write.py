import aiofiles
from typing import Optional


async def write_data(file: str, data: str, mode: str = 'a', encoding: Optional[str] = None) -> None:
    """
    Asynchronously write to a file

    Args:
        file: File name or path/to/write/file.csv, should include extension
        data: The data or expression of the date to be written i.e data = '|'.join(mylist)
        mode: Default 'a'. Usual python mode for writing, ex, w, a, w+, etc.
        encoding: Default - None ('utf-8'). Additional encoding supplied, e.g. 'latin-1'

    Returns: None

    """
    async with aiofiles.open(file, mode, encoding=encoding) as f:
        await f.write(data)
