import pytest
from .context import JsonRPC2


@pytest.fixture
def test_app():
    return JsonRPC2()
