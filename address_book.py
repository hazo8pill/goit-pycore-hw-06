"""Address book model: Field -> Name / Phone, Record, AddressBook.

Data model used by the CLI assistant bot (bot.py).

Errors are raised to match the bot's input_error decorator:
ValueError -> invalid name/phone or missing phone, KeyError -> unknown contact,
TypeError  -> argument of the wrong type (nothing is changed).
"""

import re
from collections import UserDict


def _require_str(value, what: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{what} must be a str")


class Field:
    """Base class for record fields; holds a single value."""

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Contact name. Required: must be a non-blank str."""

    def __init__(self, value):
        _require_str(value, "Name")
        if not value.strip():
            raise ValueError("Name is required")
        super().__init__(value)


class Phone(Field):
    """Phone number: exactly 10 ASCII digits, e.g. "0501234567"."""

    def __init__(self, value):
        _require_str(value, "Phone")
        if not re.fullmatch(r"[0-9]{10}", value):
            raise ValueError("Phone must be exactly 10 digits")
        super().__init__(value)


class Record:
    """A contact: one Name and a list of Phone objects."""

    def __init__(self, name):
        self.name = Name(name)
        self.phones = []

    def add_phone(self, phone: str) -> None:
        """Append a phone. Raises ValueError if it is invalid."""
        self.phones.append(Phone(phone))

    def find_phone(self, phone: str) -> Phone | None:
        """Return the Phone object with this number, or None."""
        _require_str(phone, "Phone")
        return next((p for p in self.phones if p.value == phone), None)

    def remove_phone(self, phone: str) -> None:
        """Remove a phone. Raises ValueError if the record doesn't have it."""
        self.phones.remove(self._get_phone(phone))

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """
        Replace old_phone with new_phone, keeping its position.

        Raises ValueError if old_phone is missing or new_phone is invalid;
        the record is left unchanged in both cases.
        """
        index = self.phones.index(self._get_phone(old_phone))
        self.phones[index] = Phone(new_phone)

    def _get_phone(self, phone: str) -> Phone:
        found = self.find_phone(phone)
        if found is None:
            raise ValueError(f"Phone {phone} not found")
        return found

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    """Records keyed by contact name (exact, case-sensitive match)."""

    def add_record(self, record: Record) -> None:
        """Add a record; a record with the same name is replaced."""
        if not isinstance(record, Record):
            raise TypeError("record must be a Record")
        self.data[record.name.value] = record

    def find(self, name: str) -> Record | None:
        """Return the record for name, or None."""
        _require_str(name, "Name")
        return self.data.get(name)

    def delete(self, name: str) -> None:
        """Delete the record for name. Raises KeyError if there is none."""
        _require_str(name, "Name")
        del self.data[name]


def main() -> None:
    """Run the example from the assignment."""
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
    print(john)  # Contact name: John, phones: 1112223333; 5555555555

    found_phone = john.find_phone("5555555555")
    print(f"{john.name}: {found_phone}")  # John: 5555555555

    book.delete("Jane")


if __name__ == "__main__":
    main()
