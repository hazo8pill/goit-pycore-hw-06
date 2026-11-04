# goit-pycore-hw-06 — Address book (OOP)

The CLI assistant bot from hw-05, now storing contacts in an object-oriented address book
instead of a plain `name -> phone` dict.

| File | What |
| ---- | ---- |
| `address_book.py` | data model: `Field`, `Name`, `Phone`, `Record`, `AddressBook` |
| `bot.py` | the hw-05 command-line bot, backed by `AddressBook` |
| `test_address_book.py`, `test_bot.py` | pytest tests |

## Bot (`bot.py`)

| Command | Result |
| ------- | ------ |
| `hello` | `How can I help you?` |
| `add NAME PHONE` | new contact → `Contact added.`; existing → phone added, `Contact updated.` |
| `change NAME NEW` | contact now has only `NEW` |
| `change NAME OLD NEW` | replaces one of the contact's phones |
| `phone NAME` | all phones of the contact, joined by `; ` |
| `all` | one `name: phones` line per contact, or `No contacts saved.` |
| `close` / `exit` / Ctrl-D / Ctrl-C | `Good bye!` |

Commands are case-insensitive. Names are matched case-insensitively and stored as first typed.
Bad input never stops the bot. The `input_error` decorator turns exceptions into messages:

| Exception | Message |
| --------- | ------- |
| `IndexError` (wrong number of arguments) | `Enter the argument for the command` |
| `ValueError` (bad phone, phone not found) | its own text, e.g. `Phone must be exactly 10 digits` |
| `KeyError` (unknown contact) | `Contact not found.` |
| `TypeError` (wrong argument types) | `Invalid input type.` |

```text
Enter a command: add John 1234567890
Contact added.
Enter a command: add john 5555555555
Contact updated.
Enter a command: change JOHN 1234567890 0987654321
Contact updated.
Enter a command: add Ann 123
Phone must be exactly 10 digits
Enter a command: all
John: 0987654321; 5555555555
```

## Model (`address_book.py`)

| Class                   | Role                   | Rules                                                     |
| ----------------------- | ---------------------- | --------------------------------------------------------- |
| `Field`                 | base for record fields | holds `.value`; `str(field)` is `str(value)`              |
| `Name(Field)`           | contact name           | required: non-blank `str`, else `ValueError`              |
| `Phone(Field)`          | phone number           | exactly 10 ASCII digits (`0501234567`), else `ValueError` |
| `Record`                | one contact            | `.name: Name`, `.phones: list[Phone]`                     |
| `AddressBook(UserDict)` | all contacts           | `.data` maps name -> `Record`                             |

Any argument of the wrong type (a non-`str` name or phone, a non-`Record` passed to `add_record`)
raises `TypeError` and changes nothing.

### Record

| Method                 | Result                                                                                             |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| `add_phone(phone)`     | appends a `Phone`; invalid number → `ValueError`                                                   |
| `find_phone(phone)`    | the `Phone` object, or `None`                                                                      |
| `remove_phone(phone)`  | removes it; not in record → `ValueError`                                                           |
| `edit_phone(old, new)` | replaces in place (same position); missing `old` or invalid `new` → `ValueError`, record unchanged |

### AddressBook

| Method               | Result                                               |
| -------------------- | ---------------------------------------------------- |
| `add_record(record)` | stores under `record.name.value`; same name replaces |
| `find(name)`         | the `Record`, or `None`                              |
| `delete(name)`       | removes it; unknown name → `KeyError`                |

`AddressBook` matches names exactly (`find("john")` won't find `"John"`);
the bot adds case-insensitive lookup on top.

```python
from address_book import AddressBook, Record

book = AddressBook()
john = Record("John")
john.add_phone("1234567890")
book.add_record(john)

book.find("John").edit_phone("1234567890", "1112223333")
print(book.find("John"))  # Contact name: John, phones: 1112223333
```

## Run

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python bot.py              # the bot
.venv/bin/python address_book.py     # the assignment's model example
.venv/bin/python -m pytest -v        # all tests
```
