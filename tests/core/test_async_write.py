import pytest
from core.async_write import write_data

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('data, how, encoding', [("|".join(['1', '2', '3']), 'a', None),
                                                 ("\n".join(['1', '2', '3']), 'w', None),
                                                 ("['1', '2', '3']", 'w', 'latin-1'),
                                                 ])
async def test_write_data(afs, data, how, encoding):
    filename = 'test.txt'
    await write_data(filename, data, how, encoding)
    assert afs.exists(filename)
