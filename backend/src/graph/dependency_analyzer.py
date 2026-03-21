"""Dependency analyzer for Python import statements.

Analyzes Python source code to extract import dependencies using AST.
"""

from __future__ import annotations

import ast
import logging
from pathlib import Path

from src.graph.base import DependencyInfo

logger = logging.getLogger(__name__)


class DependencyAnalyzer:
    """Analyzes Python import dependencies using AST.

    Parses Python source code and extracts all import statements,
    providing information about module dependencies, aliases, and
    specific imported names.

    Example:
        >>> analyzer = DependencyAnalyzer()
        >>> deps = analyzer.analyze("import os\\nfrom sys import path")
        >>> len(deps)
        2
        >>> deps[0].module_name
        'os'
    """

    NAME = "dependency-analyzer"

    def analyze(self, source_code: str, file_path: str | None = None) -> list[DependencyInfo]:
        """Analyze Python source code and extract dependencies.

        Args:
            source_code: Python source code to analyze
            file_path: Optional file path for context

        Returns:
            List of DependencyInfo objects representing imports

        Example:
            >>> analyzer = DependencyAnalyzer()
            >>> code = "import os\\nfrom typing import List, Dict"
            >>> deps = analyzer.analyze(code)
            >>> len(deps)
            2
        """
        if not source_code or not source_code.strip():
            return []

        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            logger.warning(f"Syntax error parsing {file_path}: {e}")
            return []

        dependencies: list[DependencyInfo] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                dependencies.extend(self._process_import(node))
            elif isinstance(node, ast.ImportFrom):
                dep = self._process_import_from(node)
                if dep:
                    dependencies.append(dep)

        return dependencies

    def analyze_file(self, file_path: str | Path) -> list[DependencyInfo]:
        """Analyze a Python file and extract dependencies.

        Args:
            file_path: Path to the Python file

        Returns:
            List of DependencyInfo objects representing imports
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return []

        try:
            source_code = path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Error reading file {file_path}: {e}")
            return []

        return self.analyze(source_code, str(path))

    def _process_import(self, node: ast.Import) -> list[DependencyInfo]:
        """Process an 'import X' statement.

        Args:
            node: AST Import node

        Returns:
            List of DependencyInfo for each imported module
        """
        dependencies: list[DependencyInfo] = []

        for alias in node.names:
            dependencies.append(
                DependencyInfo(
                    module_name=alias.name,
                    alias=alias.asname,
                    is_relative=False,
                    level=0,
                    line_number=node.lineno,
                )
            )

        return dependencies

    def _process_import_from(self, node: ast.ImportFrom) -> DependencyInfo | None:
        """Process a 'from X import Y' statement.

        Args:
            node: AST ImportFrom node

        Returns:
            DependencyInfo or None if module is None
        """
        if node.module is None:
            # Handle 'from . import X' case
            module_name = ""
        else:
            module_name = node.module

        imported_names = [alias.name for alias in node.names]
        # Use first alias's asname if present (typically all have same alias behavior)
        alias = node.names[0].asname if node.names else None

        return DependencyInfo(
            module_name=module_name,
            alias=alias,
            is_relative=node.level > 0,
            level=node.level,
            imported_names=imported_names,
            line_number=node.lineno,
        )

    def get_module_dependencies(
        self, source_code: str, exclude_stdlib: bool = False, exclude_relative: bool = False
    ) -> list[str]:
        """Get list of module names that this code depends on.

        Args:
            source_code: Python source code
            exclude_stdlib: Whether to exclude standard library modules
            exclude_relative: Whether to exclude relative imports

        Returns:
            List of unique module names
        """
        deps = self.analyze(source_code)
        modules: set[str] = set()

        for dep in deps:
            if exclude_relative and dep.is_relative:
                continue

            # Get the top-level module name
            top_level = dep.module_name.split(".")[0] if dep.module_name else ""

            if top_level:
                modules.add(top_level)

        if exclude_stdlib:
            modules = modules - self._get_stdlib_modules()

        return sorted(modules)

    def _get_stdlib_modules(self) -> set[str]:
        """Get set of Python standard library module names.

        Returns:
            Set of stdlib module names
        """
        # Common stdlib modules (not exhaustive)
        stdlib_modules = {
            "abc",
            "argparse",
            "array",
            "ast",
            "asyncio",
            "atexit",
            "base64",
            "bisect",
            "builtins",
            "bz2",
            "calendar",
            "cgi",
            "cmath",
            "cmd",
            "code",
            "codecs",
            "collections",
            "colorsys",
            "concurrent",
            "configparser",
            "contextlib",
            "copy",
            "csv",
            "dataclasses",
            "datetime",
            "dbm",
            "decimal",
            "difflib",
            "dis",
            "doctest",
            "email",
            "enum",
            "errno",
            "faulthandler",
            "fcntl",
            "filecmp",
            "fileinput",
            "fnmatch",
            "fractions",
            "ftplib",
            "functools",
            "gc",
            "getopt",
            "getpass",
            "gettext",
            "glob",
            "graphlib",
            "grp",
            "gzip",
            "hashlib",
            "heapq",
            "hmac",
            "html",
            "http",
            "imaplib",
            "importlib",
            "inspect",
            "io",
            "ipaddress",
            "itertools",
            "json",
            "keyword",
            "linecache",
            "locale",
            "logging",
            "lzma",
            "mailbox",
            "marshal",
            "math",
            "mimetypes",
            "mmap",
            "multiprocessing",
            "netrc",
            "numbers",
            "operator",
            "optparse",
            "os",
            "pathlib",
            "pdb",
            "pickle",
            "pipes",
            "pkgutil",
            "platform",
            "plistlib",
            "poplib",
            "posix",
            "posixpath",
            "pprint",
            "profile",
            "pstats",
            "pty",
            "pwd",
            "py_compile",
            "pyclbr",
            "pydoc",
            "queue",
            "quopri",
            "random",
            "re",
            "readline",
            "reprlib",
            "resource",
            "rlcompleter",
            "runpy",
            "sched",
            "secrets",
            "select",
            "selectors",
            "shelve",
            "shlex",
            "shutil",
            "signal",
            "site",
            "smtplib",
            "socket",
            "socketserver",
            "spwd",
            "sqlite3",
            "ssl",
            "stat",
            "statistics",
            "string",
            "stringprep",
            "struct",
            "subprocess",
            "sunau",
            "symtable",
            "sys",
            "sysconfig",
            "syslog",
            "tabnanny",
            "tarfile",
            "telnetlib",
            "tempfile",
            "termios",
            "test",
            "textwrap",
            "threading",
            "time",
            "timeit",
            "tkinter",
            "token",
            "tokenize",
            "trace",
            "traceback",
            "tracemalloc",
            "tty",
            "turtle",
            "types",
            "typing",
            "unicodedata",
            "unittest",
            "urllib",
            "uu",
            "uuid",
            "venv",
            "warnings",
            "wave",
            "weakref",
            "webbrowser",
            "winreg",
            "winsound",
            "wsgiref",
            "xdrlib",
            "xml",
            "xmlrpc",
            "zipapp",
            "zipfile",
            "zipimport",
            "zlib",
        }
        return stdlib_modules
