"""Unit tests for bot (hw-05 CLI assistant, now backed by AddressBook).

Contract under test (hw-05 behaviour, adapted to the hw-06 model):
- input_error: IndexError -> "Enter the argument for the command",
  ValueError -> its own message (e.g. bad phone), KeyError -> "Contact not found.",
  TypeError -> "Invalid input type."; other exceptions propagate; functools.wraps
- every command handler is wrapped by input_error
- parse_input: (cmd lowercased, *args as typed); blank -> ("",); non-str -> TypeError
- names case-insensitive, stored as first typed
- add: new name -> new record; existing name -> phone appended (no duplicates)
- change NAME NEW -> contact has only NEW; change NAME OLD NEW -> OLD replaced
- phone / all list every phone joined by "; "
- wrong arg count / unknown name / bad phone / bad types -> message, book untouched
- main: all print/input; exit/close (any case), EOF or Ctrl-C -> "Good bye!"

Run: python -m pytest -v
"""

import pytest

from address_book import AddressBook, Record
from bot import (
    add_contact,
    change_contact,
    input_error,
    main,
    parse_input,
    show_all,
    show_phone,
)

ENTER_ARG = "Enter the argument for the command"
NOT_FOUND = "Contact not found."
BAD_TYPE = "Invalid input type."
BAD_PHONE = "Phone must be exactly 10 digits"

P1, P2, P3 = "1234567890", "0987654321", "5555555555"


def make_book(**contacts):
    """make_book(John=[P1, P2]) -> AddressBook with those records."""
    book = AddressBook()
    for name, phones in contacts.items():
        record = Record(name)
        for phone in phones:
            record.add_phone(phone)
        book.add_record(record)
    return book


def snapshot(book):
    """{name: [phones]} for easy equality checks."""
    return {name: [p.value for p in r.phones] for name, r in book.data.items()}


# --- input_error -------------------------------------------------------------

def raiser(exc):
    @input_error
    def handler(*args, **kwargs):
        raise exc

    return handler


@pytest.mark.parametrize("exc, message", [
    (IndexError("list index out of range"), ENTER_ARG),
    (ValueError(BAD_PHONE), BAD_PHONE),
    (KeyError("John"), NOT_FOUND),
    (TypeError("args must be a list"), BAD_TYPE),
])
def test_decorator_maps_exceptions_to_messages(exc, message):
    assert raiser(exc)(["John"], AddressBook()) == message


def test_decorator_lets_other_exceptions_propagate():
    with pytest.raises(RuntimeError):
        raiser(RuntimeError("boom"))()


def test_decorator_passes_result_and_arguments_through():
    @input_error
    def echo(*args, **kwargs):
        return args, kwargs

    assert echo(1, 2, key="v") == ((1, 2), {"key": "v"})


@pytest.mark.parametrize("handler", [add_contact, change_contact, show_phone, show_all])
def test_every_handler_is_decorated(handler):
    assert hasattr(handler, "__wrapped__")
    assert handler.__name__ == handler.__wrapped__.__name__


# --- parse_input -------------------------------------------------------------

def test_parse_splits_command_and_args():
    assert parse_input("add John 123") == ("add", "John", "123")


def test_parse_lowercases_command_only():
    assert parse_input("ADD John 123") == ("add", "John", "123")
    assert parse_input("HeLLo") == ("hello",)


def test_parse_ignores_extra_whitespace():
    assert parse_input("   phone    John  \n") == ("phone", "John")


@pytest.mark.parametrize("line", ["", "   ", "\t\n"])
def test_parse_blank_line(line):
    assert parse_input(line) == ("",)


@pytest.mark.parametrize("bad", [None, 123, b"add", ["add", "John"]])
def test_parse_rejects_non_str(bad):
    with pytest.raises(TypeError):
        parse_input(bad)


# --- add_contact -------------------------------------------------------------

def test_add_contact():
    book = AddressBook()
    assert add_contact(["John", P1], book) == "Contact added."
    assert snapshot(book) == {"John": [P1]}
    assert isinstance(book.find("John"), Record)


def test_add_accepts_tuple_args():
    book = AddressBook()
    add_contact(("John", P1), book)
    assert snapshot(book) == {"John": [P1]}


def test_add_existing_appends_phone_and_keeps_original_casing():
    book = make_book(John=[P1])
    assert add_contact(["JOHN", P2], book) == "Contact updated."
    assert snapshot(book) == {"John": [P1, P2]}


def test_add_existing_phone_is_not_duplicated():
    book = make_book(John=[P1])
    assert add_contact(["john", P1], book) == "Contact updated."
    assert snapshot(book) == {"John": [P1]}


@pytest.mark.parametrize("phone", ["123", "phone12345", "+380501234567"])
def test_add_invalid_phone_creates_nothing(phone):
    book = make_book(Ann=[P3])
    assert add_contact(["John", phone], book) == BAD_PHONE
    assert snapshot(book) == {"Ann": [P3]}


def test_add_invalid_phone_to_existing_contact():
    book = make_book(John=[P1])
    assert add_contact(["John", "123"], book) == BAD_PHONE
    assert snapshot(book) == {"John": [P1]}


@pytest.mark.parametrize("args", [[], ["John"], ["John", P1, "extra"]])
def test_add_wrong_arg_count(args):
    book = make_book(Ann=[P3])
    assert add_contact(args, book) == ENTER_ARG
    assert snapshot(book) == {"Ann": [P3]}


# --- change_contact ----------------------------------------------------------

def test_change_replaces_all_phones_case_insensitive():
    book = make_book(John=[P1, P3])
    assert change_contact(["john", P2], book) == "Contact updated."
    assert snapshot(book) == {"John": [P2]}


def test_change_one_phone_of_many():
    book = make_book(John=[P1, P3])
    assert change_contact(["John", P1, P2], book) == "Contact updated."
    assert snapshot(book) == {"John": [P2, P3]}


def test_change_missing_old_phone():
    book = make_book(John=[P1])
    assert change_contact(["John", P3, P2], book) == f"Phone {P3} not found"
    assert snapshot(book) == {"John": [P1]}


@pytest.mark.parametrize("args", [["John", "123"], ["John", P1, "123"]])
def test_change_to_invalid_phone(args):
    book = make_book(John=[P1])
    assert change_contact(args, book) == BAD_PHONE
    assert snapshot(book) == {"John": [P1]}


def test_change_unknown_contact():
    book = make_book(John=[P1])
    assert change_contact(["Ann", P3], book) == NOT_FOUND
    assert snapshot(book) == {"John": [P1]}


@pytest.mark.parametrize("args", [[], ["John"], ["John", P1, P2, P3]])
def test_change_wrong_arg_count(args):
    book = make_book(John=[P1])
    assert change_contact(args, book) == ENTER_ARG
    assert snapshot(book) == {"John": [P1]}


# --- show_phone --------------------------------------------------------------

def test_show_phone_case_insensitive():
    assert show_phone(["JOHN"], make_book(John=[P1])) == P1


def test_show_phone_lists_all_phones():
    assert show_phone(["John"], make_book(John=[P1, P2])) == f"{P1}; {P2}"


def test_show_phone_unknown_contact():
    assert show_phone(["Ann"], make_book(John=[P1])) == NOT_FOUND


def test_show_phone_without_name():
    assert show_phone([], make_book(John=[P1])) == ENTER_ARG


def test_show_phone_ignores_extra_args():
    assert show_phone(["John", "extra"], make_book(John=[P1])) == P1


# --- show_all ----------------------------------------------------------------

def test_show_all_empty():
    assert show_all(AddressBook()) == "No contacts saved."


def test_show_all_in_insertion_order():
    book = make_book(John=[P1, P2], Ann=[P3])
    assert show_all(book) == f"John: {P1}; {P2}\nAnn: {P3}"


# --- type robustness: bad types give a message, never an exception ----------

HANDLERS = [
    (add_contact, ["John", P1]),
    (change_contact, ["John", P1]),
    (show_phone, ["John"]),
]


@pytest.mark.parametrize("handler, _", HANDLERS)
@pytest.mark.parametrize("bad_args", [None, 42, "John 123", {"John": P1}, [1, 2], ["John", None]])
def test_handlers_bad_args_type(handler, _, bad_args):
    book = make_book(John=[P3])
    assert handler(bad_args, book) == BAD_TYPE
    assert snapshot(book) == {"John": [P3]}


@pytest.mark.parametrize("handler, good_args", HANDLERS)
@pytest.mark.parametrize("bad_book", [None, [], {"John": P1}, "John:123"])
def test_handlers_bad_book_type(handler, good_args, bad_book):
    assert handler(good_args, bad_book) == BAD_TYPE


@pytest.mark.parametrize("bad_book", [None, [], {"John": P1}, "John:123"])
def test_show_all_bad_book_type(bad_book):
    assert show_all(bad_book) == BAD_TYPE


# --- main --------------------------------------------------------------------

def run_session(monkeypatch, capsys, lines):
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(feed))
    feed = iter(lines)
    main()
    return capsys.readouterr().out.splitlines()


def test_main_assignment_example_dialog(monkeypatch, capsys):
    out = run_session(monkeypatch, capsys, [
        "add",
        "add Bob",
        "add Jime 0501234356",
        "phone",
        "all",
        "exit",
    ])
    assert out == [
        "Welcome to the assistant bot!",
        ENTER_ARG,
        ENTER_ARG,
        "Contact added.",
        ENTER_ARG,
        "Jime: 0501234356",
        "Good bye!",
    ]


def test_main_full_session(monkeypatch, capsys):
    out = run_session(monkeypatch, capsys, [
        "hello",
        f"add John {P1}",
        f"add john {P3}",
        f"change JOHN {P1} {P2}",
        "phone JOHN",
        "phone Ann",
        f"change Ann {P3}",
        "add Ann 555",
        f"add Ann {P3}",
        "all",
        "exit",
    ])
    assert out == [
        "Welcome to the assistant bot!",
        "How can I help you?",
        "Contact added.",
        "Contact updated.",
        "Contact updated.",
        f"{P2}; {P3}",
        NOT_FOUND,
        NOT_FOUND,
        BAD_PHONE,
        "Contact added.",
        f"John: {P2}; {P3}",
        f"Ann: {P3}",
        "Good bye!",
    ]


@pytest.mark.parametrize("word", ["close", "CLOSE", "Exit"])
def test_main_exit_words_any_case(monkeypatch, capsys, word):
    out = run_session(monkeypatch, capsys, [word, "hello"])
    assert out == ["Welcome to the assistant bot!", "Good bye!"]


def test_main_invalid_and_blank_commands(monkeypatch, capsys):
    out = run_session(monkeypatch, capsys, ["test", "", "exit"])
    assert out[1:] == ["Invalid command.", "Invalid command.", "Good bye!"]


@pytest.mark.parametrize("exc", [EOFError, KeyboardInterrupt])
def test_main_eof_or_ctrl_c_exits(monkeypatch, capsys, exc):
    def raise_exc(_prompt=""):
        raise exc

    monkeypatch.setattr("builtins.input", raise_exc)
    main()
    assert capsys.readouterr().out.splitlines()[-1] == "Good bye!"
