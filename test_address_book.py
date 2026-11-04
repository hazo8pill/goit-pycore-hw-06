"""Unit tests for address_book (Field / Name / Phone / Record / AddressBook).

Contract under test:
- Field keeps .value; str(field) == str(value)
- Name is required: blank -> ValueError
- Phone is exactly 10 ASCII digits, otherwise ValueError
- wrong argument types anywhere (non-str name/phone, non-Record) -> TypeError,
  nothing changed
- Record: .name is Name, .phones is list[Phone];
  add_phone / find_phone (Phone or None) / remove_phone / edit_phone;
  missing phone or invalid new phone -> ValueError, record left unchanged
- AddressBook (UserDict): add_record keys by name, find -> Record or None,
  delete removes, missing name -> KeyError; names match exactly (case-sensitive)
- the assignment's example script prints the expected output

Run: python -m pytest -v
"""

from collections import UserDict

import pytest

from address_book import AddressBook, Field, Name, Phone, Record


# --- Field / Name ------------------------------------------------------------

def test_field_stores_value_and_str():
    field = Field(42)
    assert field.value == 42
    assert str(field) == "42"


def test_name_is_field():
    name = Name("John")
    assert isinstance(name, Field)
    assert name.value == "John"
    assert str(name) == "John"


@pytest.mark.parametrize("bad", ["", "   "])
def test_name_required(bad):
    with pytest.raises(ValueError):
        Name(bad)


@pytest.mark.parametrize("bad", [None, 123, ["John"]])
def test_name_must_be_str(bad):
    with pytest.raises(TypeError):
        Name(bad)


# --- Phone -------------------------------------------------------------------

def test_phone_valid():
    phone = Phone("0501234567")
    assert isinstance(phone, Field)
    assert phone.value == "0501234567"
    assert str(phone) == "0501234567"


@pytest.mark.parametrize(
    "bad",
    [
        "",
        "123456789",          # 9 digits
        "12345678901",        # 11 digits
        "12345abcde",         # letters
        "+380501234",         # plus sign
        "050 123 456",        # spaces
        "050-123-45-67",      # dashes
        " 0501234567",        # surrounding whitespace
        "0501234567\n",       # trailing newline
        "١٢٣٤٥٦٧٨٩٠",         # Arabic-Indic digits: isdigit() is True, still invalid
    ],
)
def test_phone_invalid(bad):
    with pytest.raises(ValueError):
        Phone(bad)


@pytest.mark.parametrize("bad", [1234567890, None, b"1234567890"])
def test_phone_must_be_str(bad):
    with pytest.raises(TypeError):
        Phone(bad)


# --- Record ------------------------------------------------------------------

def make_record(*phones):
    record = Record("John")
    for phone in phones:
        record.add_phone(phone)
    return record


def values(record):
    return [p.value for p in record.phones]


def test_record_init():
    record = Record("John")
    assert isinstance(record.name, Name)
    assert record.name.value == "John"
    assert record.phones == []


def test_record_requires_name():
    with pytest.raises(ValueError):
        Record("")


def test_add_phone_stores_phone_objects_in_order():
    record = make_record("1234567890", "5555555555")
    assert all(isinstance(p, Phone) for p in record.phones)
    assert values(record) == ["1234567890", "5555555555"]


def test_add_invalid_phone_leaves_record_unchanged():
    record = make_record("1234567890")
    with pytest.raises(ValueError):
        record.add_phone("123")
    assert values(record) == ["1234567890"]


def test_find_phone_returns_phone_object():
    record = make_record("1234567890", "5555555555")
    found = record.find_phone("5555555555")
    assert isinstance(found, Phone)
    assert found is record.phones[1]


def test_find_phone_missing_returns_none():
    assert make_record("1234567890").find_phone("5555555555") is None


def test_remove_phone():
    record = make_record("1234567890", "5555555555")
    record.remove_phone("1234567890")
    assert values(record) == ["5555555555"]


def test_remove_missing_phone():
    record = make_record("1234567890")
    with pytest.raises(ValueError):
        record.remove_phone("5555555555")
    assert values(record) == ["1234567890"]


def test_edit_phone_keeps_position():
    record = make_record("1234567890", "5555555555")
    record.edit_phone("1234567890", "1112223333")
    assert values(record) == ["1112223333", "5555555555"]
    assert all(isinstance(p, Phone) for p in record.phones)


def test_edit_missing_phone():
    record = make_record("1234567890")
    with pytest.raises(ValueError):
        record.edit_phone("5555555555", "1112223333")
    assert values(record) == ["1234567890"]


def test_edit_to_invalid_phone_leaves_record_unchanged():
    record = make_record("1234567890")
    with pytest.raises(ValueError):
        record.edit_phone("1234567890", "bad")
    assert values(record) == ["1234567890"]


def test_record_str():
    assert str(make_record("1112223333", "5555555555")) == (
        "Contact name: John, phones: 1112223333; 5555555555"
    )


def test_record_str_without_phones():
    assert str(Record("John")) == "Contact name: John, phones: "


# --- AddressBook -------------------------------------------------------------

def test_book_is_userdict():
    book = AddressBook()
    assert isinstance(book, UserDict)
    assert book.data == {}


def test_add_record_keys_by_name():
    book = AddressBook()
    record = Record("John")
    book.add_record(record)
    assert book.data == {"John": record}


def test_add_record_same_name_overwrites():
    book = AddressBook()
    book.add_record(Record("John"))
    newer = make_record("1234567890")
    book.add_record(newer)
    assert len(book) == 1
    assert book.find("John") is newer


def test_find():
    book = AddressBook()
    record = Record("John")
    book.add_record(record)
    assert book.find("John") is record


def test_find_missing_returns_none():
    assert AddressBook().find("John") is None


def test_find_is_case_sensitive():
    book = AddressBook()
    book.add_record(Record("John"))
    assert book.find("john") is None


def test_delete():
    book = AddressBook()
    book.add_record(Record("John"))
    book.add_record(Record("Jane"))
    book.delete("Jane")
    assert list(book.data) == ["John"]


def test_delete_missing_raises_key_error():
    book = AddressBook()
    book.add_record(Record("John"))
    with pytest.raises(KeyError):
        book.delete("Jane")
    assert list(book.data) == ["John"]


# --- wrong argument types -> TypeError, nothing changed ----------------------

@pytest.mark.parametrize("call", [
    lambda r: r.add_phone(1234567890),
    lambda r: r.find_phone(1234567890),
    lambda r: r.remove_phone(None),
    lambda r: r.edit_phone(1234567890, "1112223333"),
    lambda r: r.edit_phone("1234567890", 1112223333),
])
def test_record_methods_reject_non_str(call):
    record = make_record("1234567890")
    with pytest.raises(TypeError):
        call(record)
    assert values(record) == ["1234567890"]


@pytest.mark.parametrize("bad", ["John", None, {"John": "1234567890"}])
def test_add_record_rejects_non_record(bad):
    book = AddressBook()
    with pytest.raises(TypeError):
        book.add_record(bad)
    assert book.data == {}


@pytest.mark.parametrize("method", ["find", "delete"])
@pytest.mark.parametrize("bad", [None, 123, ["John"]])
def test_book_lookup_rejects_non_str(method, bad):
    book = AddressBook()
    book.add_record(Record("John"))
    with pytest.raises(TypeError):
        getattr(book, method)(bad)
    assert list(book.data) == ["John"]


# --- assignment example ------------------------------------------------------

def test_assignment_example(capsys):
    book = AddressBook()

    john_record = Record("John")
    john_record.add_phone("1234567890")
    john_record.add_phone("5555555555")
    book.add_record(john_record)

    jane_record = Record("Jane")
    jane_record.add_phone("9876543210")
    book.add_record(jane_record)

    for name, record in book.data.items():
        print(record)

    john = book.find("John")
    john.edit_phone("1234567890", "1112223333")
    print(john)

    found_phone = john.find_phone("5555555555")
    print(f"{john.name}: {found_phone}")

    book.delete("Jane")

    assert capsys.readouterr().out.splitlines() == [
        "Contact name: John, phones: 1234567890; 5555555555",
        "Contact name: Jane, phones: 9876543210",
        "Contact name: John, phones: 1112223333; 5555555555",
        "John: 5555555555",
    ]
    assert list(book.data) == ["John"]
