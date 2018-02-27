import pytest

from .context import JsonRPC2


@pytest.fixture
def test_app():
    return JsonRPC2()


def test_empty_method_table(test_app):
    assert len(test_app.methods) == 0


def test_add_method_with_decorator(test_app):
    @test_app.rpc_call
    def test_func():
        pass

    assert len(test_app.methods) == 1
    assert 'test_func' in test_app.methods


def test_add_method(test_app):
    def test_func():
        pass

    test_app.add_method(test_func)

    assert len(test_app.methods) == 1
    assert 'test_func' in test_app.methods
