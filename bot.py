"""Console assistant bot (hw-05) backed by the hw-06 AddressBook.

Commands:
    hello
    add NAME PHONE           new contact, or add another phone to an existing one
    change NAME NEW          contact now has only NEW
    change NAME OLD NEW      replace one of the contact's phones
    phone NAME               all phones of the contact
    all                      every contact
    close / exit             quit (also Ctrl-D / Ctrl-C)

Commands are case-insensitive; names are matched case-insensitively but
stored as first typed. Phones must be exactly 10 digits.

Command handlers raise on bad input; the input_error decorator turns those
exceptions into messages for the user, so the bot never stops on bad input.
"""

from functools import wraps

from address_book import AddressBook, Phone, Record


def input_error(func):
    """
    Turn user-input exceptions raised by a command handler into messages.

    IndexError -> "Enter the argument for the command"   (wrong arg count)
    ValueError -> the exception's own message           (bad phone, phone not found)
    KeyError   -> "Contact not found."
    TypeError  -> "Invalid input type."
    Any other exception propagates unchanged.
    """

    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IndexError:
            return "Enter the argument for the command"
        except ValueError as e:
            return str(e)
        except KeyError:
            return "Contact not found."
        except TypeError:
            return "Invalid input type."

    return inner


def _check_types(args, book) -> None:
    """Raise TypeError unless args is a list/tuple of str and book is an AddressBook."""
    if not isinstance(args, (list, tuple)) or not all(isinstance(a, str) for a in args):
        raise TypeError("args must be a list or tuple of str")
    if not isinstance(book, AddressBook):
        raise TypeError("book must be an AddressBook")


def _check_count(args, *counts: int) -> None:
    """Raise IndexError unless len(args) is one of counts."""
    if len(args) not in counts:
        raise IndexError("wrong number of arguments")


def _find_record(name: str, book: AddressBook) -> Record | None:
    """Return the record whose name matches case-insensitively, or None."""
    folded = name.casefold()
    return next((r for key, r in book.data.items() if key.casefold() == folded), None)


def _get_record(name: str, book: AddressBook) -> Record:
    """Like _find_record, but raise KeyError if there is no such contact."""
    record = _find_record(name, book)
    if record is None:
        raise KeyError(name)
    return record


def _phones(record: Record) -> str:
    return "; ".join(p.value for p in record.phones)


def parse_input(user_input: str) -> tuple[str, ...]:
    """
    Split a command line into a lowercased command and its arguments.

    Returns (command, *args); arguments keep their casing. A blank line gives ("",).
    Raises TypeError if user_input is not a str.
    """
    if not isinstance(user_input, str):
        raise TypeError("user_input must be a str")
    cmd, *args = user_input.split() or [""]
    return cmd.lower(), *args


@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    """
    add NAME PHONE: create the contact, or add PHONE to an existing one.

    Returns "Contact added." for a new contact, "Contact updated." otherwise.
    A phone the contact already has is not added twice.
    """
    _check_types(args, book)
    _check_count(args, 2)
    name, phone = args
    record = _find_record(name, book)
    if record is None:
        record = Record(name)
        record.add_phone(phone)  
        book.add_record(record)
        return "Contact added."
    if record.find_phone(phone) is None:
        record.add_phone(phone)
    return "Contact updated."


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    """
    change NAME NEW      -> the contact's phones become just NEW
    change NAME OLD NEW  -> OLD is replaced by NEW

    Returns "Contact updated."; the book changes only on success.
    """
    _check_types(args, book)
    _check_count(args, 2, 3)
    name, *phones = args
    record = _get_record(name, book)
    if len(phones) == 1:
        record.phones = [Phone(phones[0])]
    else:
        record.edit_phone(*phones)
    return "Contact updated."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    """phone NAME: the contact's phones joined by "; ". Extra args are ignored."""
    _check_types(args, book)
    return _phones(_get_record(args[0], book))


@input_error
def show_all(book: AddressBook) -> str:
    """One "name: phones" line per contact, or "No contacts saved." if empty."""
    _check_types([], book)
    if not book:
        return "No contacts saved."
    return "\n".join(f"{name}: {_phones(record)}" for name, record in book.data.items())


def main() -> None:
    """Run the bot's input loop until close/exit, Ctrl-D or Ctrl-C."""
    book = AddressBook()
    print("Welcome to the assistant bot!")
    while True:
        try:
            user_input = input("Enter a command: ")
        except (EOFError, KeyboardInterrupt):
            print("\nGood bye!")
            break
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
