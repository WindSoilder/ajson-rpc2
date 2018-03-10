import pytest
from ..context import FixedList


@pytest.fixture
def test_list():
    return FixedList(int)


def test_initialize_list():
    test_list = FixedList(int)
    assert test_list.item_type is int


def test_append_list(test_list):
    test_list.append(3)
    assert test_list[0] == 3


def test_append_list_with_wrong_type(test_list):
    with pytest.raises(TypeError):
        test_list.append("this is a string")


def test_insert_list(test_list):
    test_list.append(3)
    test_list.append(4)
    test_list.insert(0, 5)
    test_list.insert(1, 7)
    test_list.insert(4, 9)
    # the content of test list should be [5, 7, 3, 4, 9]
    assert test_list[0] == 5
    assert test_list[1] == 7
    assert test_list[3] == 4
    assert test_list[4] == 9


def test_insert_list_with_wrong_type(test_list):
    with pytest.raises(TypeError):
        test_list.insert(0, "test")

    test_list.append(3)
    test_list.append(5)
    with pytest.raises(TypeError):
        test_list.insert(1, "test type")

    with pytest.raises(TypeError):
        test_list.insert(2, "test type")


def test_extend_list(test_list):
    inserted_generator = range(10)
    test_list.extend(inserted_generator)

    assert test_list == list(range(10))


def test_extend_list_with_wrong_type(test_list):
    inserted_tuple = (1, "test", 3)
    with pytest.raises(TypeError):
        test_list.extend(inserted_tuple)

    with pytest.raises(TypeError):
        test_list.extend(["test1"])

    with pytest.raises(TypeError):
        test_list.extend(['test1', 'test3', 'test5'])
