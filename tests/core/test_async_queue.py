import pytest
from core import async_queue

pytestmark = pytest.mark.asyncio


@pytest.fixture
def queue(request):
    return async_queue.get_queue(request.param)


@pytest.mark.parametrize('maxsize', [0, 5, -1])
def test_get_queue(maxsize):
    queue = async_queue.get_queue(maxsize)
    assert queue.maxsize == maxsize


@pytest.mark.parametrize('queue', [0, 1], indirect=True)
@pytest.mark.parametrize('qitem', [(0, 1)])
async def test_set_onto_queue(queue, qitem):
    queue = await async_queue.set_onto_queue(queue, qitem)
    if queue.maxsize == 1:
        assert queue.full()
    assert queue.qsize() == 1


@pytest.mark.parametrize('queue', [0], indirect=True)
@pytest.mark.parametrize('qitem', [0,
                                   [0, 1, 2],
                                   (0, 1, 2),
                                   {0, 1, 2},
                                   {0: 1, 2: 3},
                                   None,
                                   False,
                                   'hello world',
                                   b'hello world'])
async def test_get_from_queue(queue, qitem):
    assert queue.empty()
    queue = await async_queue.set_onto_queue(queue, qitem)
    item = await async_queue.get_from_queue(queue)
    assert item == qitem
    assert queue.empty()


@pytest.mark.parametrize('queue', [0], indirect=True)
@pytest.mark.parametrize('many_qitems', [[0,
                                   [0, 1, 2],
                                   (0, 1, 2),
                                   {0, 1, 2},
                                   {0: 1, 2: 3},
                                   None,
                                   False,
                                   'hello world',
                                   b'hello world']])
async def test_set_many_onto_queue(queue, many_qitems):
    queue = await async_queue.set_many_onto_queue(queue, many_qitems)
    assert queue.qsize() == len(many_qitems)
