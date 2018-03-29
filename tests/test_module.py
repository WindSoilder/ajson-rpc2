import pytest
from .context import Module, JsonRPC2


@pytest.fixture
def test_module_name():
    return "document"


@pytest.fixture
def test_module(test_module_name):
    return Module(test_module_name)


def test_register_module(test_app: JsonRPC2, test_module: Module,
                         test_module_name: str):
    test_app.register_module(test_module)
    assert test_app.modules[test_module_name] is test_module


def test_get_method_when_method_is_registered_in_module(test_app: JsonRPC2,
                                                        test_module: Module,
                                                        test_module_name: str):
    def add(num1, num2):
        pass

    test_module.add_method(add)
    test_app.register_module(test_module)

    for valid_method in (f"{test_module_name}/add", f"{test_module_name}.add"):
        assert test_app.get_method(valid_method) is add


def test_get_method_when_give_invalid_method_name(test_app: JsonRPC2,
                                                  test_module: Module,
                                                  test_module_name: str):

    def add(num1, num2):
        pass

    test_module.add_method(add)
    test_app.register_module(test_module)

    with pytest.raises(ValueError):
        for invalid_method in ("document.open.add", "document..open"):
            test_app.get_method(invalid_method)
