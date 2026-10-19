# DNS Toolkit

A terminal-based DNS configuration toolkit built with Python,
Textual, and dnspython.

DNS Toolkit aims to simplify authoritative DNS administration
by providing a guided interface for managing DNS zones, SOA
metadata, nameservers, and resource records.

## Features

- DNS zone management
- Resource record management
- BIND 9 zone-file generation
- DNS configuration validation
- DNS lookup diagnostics
- Preview-first configuration workflow

## Technology Stack

- Python 3.12+
- uv
- Textual
- dnspython
- Ruff

## Development Setup

Install uv and Python 3.12 or a compatible interpreter.

Install the project dependencies:

    uv sync

Run the application:

    uv run dns-toolkit

Check code quality:

    uv run ruff check .
    uv run ruff format --check .

## Safety

The initial version generates and validates configuration
without automatically modifying live DNS configuration.

Applying changes to a system DNS server will require explicit
confirmation and appropriate privileges.

## License

To be determined.
