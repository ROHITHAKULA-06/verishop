"""L6 Storage tests."""
import pytest
from app.layers.l6_storage.product_store import ProductStore
from app.layers.l6_storage.vector_store import VectorStore

def test_product_store_init():
    store = ProductStore(db_path="./data/test_l6.db")
    assert store is not None

@pytest.mark.asyncio
async def test_product_store_save_and_get(sample_product):
    store = ProductStore(db_path="./data/test_l6_save.db")
    pid = await store.save_product(sample_product)
    assert pid
    retrieved = await store.get_product(pid)
    assert retrieved is not None
    assert retrieved.title == sample_product.title

def test_vector_store_init():
    vs = VectorStore(dimension=128, index_path="./data/test_vs")
    assert vs.count() == 0

def test_vector_store_add_search():
    vs = VectorStore(dimension=4, index_path="./data/test_vs2")
    vs.add([[1, 0, 0, 0], [0, 1, 0, 0]], ["id1", "id2"])
    assert vs.count() == 2
    results = vs.search([1, 0, 0, 0], top_k=1)
    assert len(results) > 0
    assert results[0][0] == "id1"
