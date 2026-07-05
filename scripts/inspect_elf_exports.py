"""Inspect exported ELF symbols without requiring readelf or objdump."""

from __future__ import annotations

import argparse
import hashlib
import struct
from dataclasses import dataclass
from pathlib import Path

SHT_SYMTAB = 2
SHT_DYNSYM = 11


@dataclass(frozen=True, slots=True)
class Section:
    """ELF section metadata needed for symbol-table parsing."""

    index: int
    name: str
    section_type: int
    flags: int
    address: int
    offset: int
    size: int
    link: int
    entry_size: int


@dataclass(frozen=True, slots=True)
class SymbolTable:
    """Parsed symbol names for one ELF symbol table."""

    path: Path
    table_name: str
    symbols: tuple[Symbol, ...]

    @property
    def names(self) -> tuple[str, ...]:
        """Return decoded symbol names for backward-compatible callers."""
        return tuple(symbol.name for symbol in self.symbols)


@dataclass(frozen=True, slots=True)
class Symbol:
    """Decoded ELF symbol metadata."""

    name: str
    value: int
    size: int
    info: int
    other: int
    section_index: int

    @property
    def binding(self) -> str:
        """Return the ELF symbol binding."""
        return _SYMBOL_BINDINGS.get(self.info >> 4, str(self.info >> 4))

    @property
    def symbol_type(self) -> str:
        """Return the ELF symbol type."""
        return _SYMBOL_TYPES.get(self.info & 0x0F, str(self.info & 0x0F))


@dataclass(frozen=True, slots=True)
class SymbolBytes:
    """Raw bytes for one ELF symbol mapped through its section."""

    path: Path
    symbol: Symbol
    section: Section
    file_offset: int
    body: bytes

    @property
    def mapped_address(self) -> int:
        """Return the address used to map this symbol to a section."""
        return self.symbol.value & ~1

    @property
    def thumb_entry(self) -> bool:
        """Return whether this ARM symbol value uses the Thumb entry bit."""
        return bool(self.symbol.value & 1)

    @property
    def sha256_hex(self) -> str:
        """Return a stable SHA-256 digest for the symbol body."""
        return hashlib.sha256(self.body).hexdigest()

    def first_hex(self, length: int) -> str:
        """Return the first bytes as space-separated hex."""
        return self.body[:length].hex(" ")

    def last_hex(self, length: int) -> str:
        """Return the last bytes as space-separated hex."""
        return self.body[-length:].hex(" ") if self.body else ""


_SYMBOL_BINDINGS = {
    0: "LOCAL",
    1: "GLOBAL",
    2: "WEAK",
    10: "LOOS",
    12: "HIOS",
    13: "LOPROC",
    15: "HIPROC",
}
_SYMBOL_TYPES = {
    0: "NOTYPE",
    1: "OBJECT",
    2: "FUNC",
    3: "SECTION",
    4: "FILE",
    5: "COMMON",
    6: "TLS",
    10: "LOOS",
    12: "HIOS",
    13: "LOPROC",
    15: "HIPROC",
}


def _c_string(blob: bytes, offset: int) -> str:
    if offset >= len(blob):
        return ""
    end = blob.find(b"\0", offset)
    if end < 0:
        end = len(blob)
    return blob[offset:end].decode("utf-8", "replace")


def _parse_sections(data: bytes) -> tuple[str, int, list[Section]]:
    if data[:4] != b"\x7fELF":
        raise ValueError("not an ELF file")

    elf_class = data[4]
    endian = "<" if data[5] == 1 else ">"

    if elf_class == 1:
        section_offset = struct.unpack_from(endian + "I", data, 32)[0]
        section_entry_size = struct.unpack_from(endian + "H", data, 46)[0]
        section_count = struct.unpack_from(endian + "H", data, 48)[0]
        section_string_index = struct.unpack_from(endian + "H", data, 50)[0]
        header_format = endian + "IIIIIIIIII"
    elif elf_class == 2:
        section_offset = struct.unpack_from(endian + "Q", data, 40)[0]
        section_entry_size = struct.unpack_from(endian + "H", data, 58)[0]
        section_count = struct.unpack_from(endian + "H", data, 60)[0]
        section_string_index = struct.unpack_from(endian + "H", data, 62)[0]
        header_format = endian + "IIQQQQIIQQ"
    else:
        raise ValueError(f"unsupported ELF class: {elf_class}")

    raw_sections: list[tuple[int, int, int, int, int, int, int, int]] = []
    for index in range(section_count):
        offset = section_offset + index * section_entry_size
        header = struct.unpack_from(header_format, data, offset)
        raw_sections.append(
            (
                header[0],
                header[1],
                header[2],
                header[3],
                header[4],
                header[5],
                header[6],
                header[9],
            )
        )

    string_header = raw_sections[section_string_index]
    section_strings = data[string_header[4] : string_header[4] + string_header[5]]

    return endian, elf_class, [
        Section(
            index=index,
            name=_c_string(section_strings, name_offset),
            section_type=section_type,
            flags=flags,
            address=address,
            offset=offset,
            size=size,
            link=link,
            entry_size=entry_size,
        )
        for index, (
            name_offset,
            section_type,
            flags,
            address,
            offset,
            size,
            link,
            entry_size,
        )
        in enumerate(raw_sections)
    ]


def read_symbol_tables(path: Path) -> tuple[SymbolTable, ...]:
    """Return every static and dynamic symbol table with decoded names."""
    data = path.read_bytes()
    endian, elf_class, sections = _parse_sections(data)
    tables: list[SymbolTable] = []

    for section in sections:
        if section.section_type not in {SHT_SYMTAB, SHT_DYNSYM}:
            continue
        if not (0 <= section.link < len(sections)):
            continue
        strings = sections[section.link]
        string_blob = data[strings.offset : strings.offset + strings.size]
        entry_size = section.entry_size or (16 if elf_class == 1 else 24)
        symbols: list[Symbol] = []

        for symbol_index in range(section.size // entry_size):
            symbol_offset = section.offset + symbol_index * entry_size
            if elf_class == 1:
                name_offset, value, size, info, other, section_index = (
                    struct.unpack_from(endian + "IIIBBH", data, symbol_offset)
                )
            else:
                name_offset, info, other, section_index, value, size = (
                    struct.unpack_from(endian + "IBBHQQ", data, symbol_offset)
                )
            name = _c_string(string_blob, name_offset)
            if name:
                symbols.append(
                    Symbol(
                        name=name,
                        value=value,
                        size=size,
                        info=info,
                        other=other,
                        section_index=section_index,
                    )
                )

        tables.append(
            SymbolTable(path=path, table_name=section.name, symbols=tuple(symbols))
        )

    return tuple(tables)


def read_symbol_bytes(
    path: Path,
    names: tuple[str, ...],
    *,
    table_name: str = ".dynsym",
) -> dict[str, SymbolBytes]:
    """Return raw bytes for named symbols in an ELF symbol table."""
    data = path.read_bytes()
    _endian, _elf_class, sections = _parse_sections(data)
    table = next(
        (
            table
            for table in read_symbol_tables(path)
            if table.table_name == table_name
        ),
        None,
    )
    if table is None:
        raise ValueError(f"{path} does not expose {table_name}")

    wanted = set(names)
    result: dict[str, SymbolBytes] = {}
    for symbol in table.symbols:
        if symbol.name not in wanted:
            continue
        if not (0 <= symbol.section_index < len(sections)):
            continue
        section = sections[symbol.section_index]
        mapped_address = symbol.value & ~1
        if not (
            section.address <= mapped_address < section.address + section.size
        ):
            continue
        file_offset = section.offset + (mapped_address - section.address)
        result[symbol.name] = SymbolBytes(
            path=path,
            symbol=symbol,
            section=section,
            file_offset=file_offset,
            body=data[file_offset : file_offset + symbol.size],
        )
    return result


def _matches(name: str, filters: tuple[str, ...]) -> bool:
    if not filters:
        return True
    folded = name.casefold()
    return any(pattern.casefold() in folded for pattern in filters)


def _sort_symbols(symbols: tuple[Symbol, ...], sort: str) -> tuple[Symbol, ...]:
    if sort == "value":
        return tuple(sorted(symbols, key=lambda symbol: (symbol.value, symbol.name)))
    if sort == "size":
        return tuple(
            sorted(symbols, key=lambda symbol: (symbol.size, symbol.name), reverse=True)
        )
    if sort == "type":
        return tuple(
            sorted(
                symbols,
                key=lambda symbol: (symbol.symbol_type, symbol.binding, symbol.name),
            )
        )
    return tuple(sorted(symbols, key=lambda symbol: symbol.name.casefold()))


def _format_symbol(symbol: Symbol, *, details: bool) -> str:
    if not details:
        return symbol.name
    return (
        f"{symbol.value:#010x} {symbol.size:>6} "
        f"{symbol.binding:<6} {symbol.symbol_type:<7} {symbol.name}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument(
        "--contains",
        action="append",
        default=[],
        help="case-insensitive substring filter; may be passed multiple times",
    )
    parser.add_argument(
        "--table",
        choices=("all", "dynsym", "symtab"),
        default="all",
        help="symbol table type to print",
    )
    parser.add_argument(
        "--sort",
        choices=("name", "value", "size", "type"),
        default="name",
        help="sort matching symbols before printing",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="print value, size, binding, and symbol type",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=0,
        help="only print symbols with at least this byte size",
    )
    parser.add_argument(
        "--bytes",
        action="store_true",
        help=(
            "also print section, file offset, Thumb bit, SHA-256, and first/"
            "last 16 bytes for matching symbols"
        ),
    )
    parser.add_argument("--names-only", action="store_true")
    args = parser.parse_args()

    wanted_table = {
        "all": None,
        "dynsym": ".dynsym",
        "symtab": ".symtab",
    }[args.table]

    filters = tuple(args.contains)
    for path in args.paths:
        for table in read_symbol_tables(path):
            if wanted_table is not None and table.table_name != wanted_table:
                continue
            symbols = tuple(
                symbol
                for symbol in table.symbols
                if symbol.size >= args.min_size and _matches(symbol.name, filters)
            )
            symbols = _sort_symbols(symbols, args.sort)
            if not args.names_only:
                print(f"{path}: {table.table_name}: {len(symbols)} symbols")
            symbol_bytes = (
                read_symbol_bytes(path, tuple(symbol.name for symbol in symbols))
                if args.bytes
                else {}
            )
            for symbol in symbols:
                if args.names_only:
                    print(symbol.name)
                else:
                    print(f"  {_format_symbol(symbol, details=args.details)}")
                    body = symbol_bytes.get(symbol.name)
                    if body is not None:
                        print(
                            "    "
                            f"section={body.section.name} "
                            f"file_offset={body.file_offset:#010x} "
                            f"thumb={body.thumb_entry} "
                            f"sha256={body.sha256_hex}"
                        )
                        print(f"    first16={body.first_hex(16)}")
                        print(f"    last16={body.last_hex(16)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
