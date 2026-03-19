"""Tests for AST-based chunkers.

Test cases:
- TC-2.2.1: PythonASTChunker 按函数/类切分
- TC-2.2.2: TypeScriptASTChunker 按函数/类/方法切分
- TC-2.2.3: GoASTChunker 按函数/方法/类型切分
- TC-2.2.4: AST chunkers 注册到 ChunkerRegistry
"""

import sys
from pathlib import Path

import pytest

# Add src to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestPythonASTChunker:
    """TC-2.2.1: PythonASTChunker 按函数/类切分"""

    def test_splits_functions(self):
        """TC-2.2.1: Functions are split as separate chunks."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
def hello():
    print("Hello")

def world():
    print("World")
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 2
        assert "def hello()" in chunks[0].text
        assert "def world()" in chunks[1].text

    def test_splits_classes(self):
        """TC-2.2.1: Classes are split as separate chunks."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
class MyClass:
    pass

class OtherClass:
    pass
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 2
        assert "class MyClass" in chunks[0].text
        assert "class OtherClass" in chunks[1].text

    def test_extracts_function_name(self):
        """TC-2.2.1: Function name is extracted in metadata."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
def my_function():
    pass
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 1
        assert chunks[0].metadata["name"] == "my_function"
        assert chunks[0].metadata["node_type"] == "function_definition"

    def test_extracts_class_name(self):
        """TC-2.2.1: Class name is extracted in metadata."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
class MyClass:
    pass
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 1
        assert chunks[0].metadata["name"] == "MyClass"
        assert chunks[0].metadata["node_type"] == "class_definition"

    def test_line_positions_accurate(self):
        """TC-2.2.1: Line positions are accurate."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''def hello():
    pass

def world():
    pass
'''
        chunks = chunker.chunk(code)
        
        assert chunks[0].metadata["start_line"] == 1
        assert chunks[0].metadata["end_line"] == 2
        assert chunks[1].metadata["start_line"] == 4
        assert chunks[1].metadata["end_line"] == 5

    def test_empty_code_returns_empty_list(self):
        """Empty code returns empty list."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        chunks = chunker.chunk("")
        
        assert chunks == []

    def test_whitespace_only_returns_empty_list(self):
        """Whitespace-only code returns empty list."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        chunks = chunker.chunk("   \n\n   ")
        
        assert chunks == []

    def test_no_definitions_returns_single_chunk(self):
        """Code without functions/classes returns single chunk."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''# Just a comment
x = 1
y = 2
'''
        chunks = chunker.chunk(code)
        
        # No function/class definitions, returns single chunk
        assert len(chunks) == 1
        assert chunks[0].metadata["node_type"] == "source_file"

    def test_supports_language_check(self):
        """PythonASTChunker supports python and py languages."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        assert chunker.supports_language("python") is True
        assert chunker.supports_language("py") is True
        assert chunker.supports_language("PYTHON") is True  # case-insensitive
        assert chunker.supports_language("typescript") is False

    def test_nested_functions(self):
        """Nested functions are handled correctly."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
def outer():
    def inner():
        pass
    pass
'''
        chunks = chunker.chunk(code)
        
        # Only top-level function is chunked
        assert len(chunks) >= 1
        assert "def outer()" in chunks[0].text


class TestTypeScriptASTChunker:
    """TC-2.2.2: TypeScriptASTChunker 按函数/类/方法切分"""

    def test_splits_functions(self):
        """TC-2.2.2: Functions are split as separate chunks."""
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker = TypeScriptASTChunker()
        
        code = '''
function hello(): void {
    console.log("Hello");
}

function world(): void {
    console.log("World");
}
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 2
        assert "function hello" in chunks[0].text
        assert "function world" in chunks[1].text

    def test_splits_classes(self):
        """TC-2.2.2: Classes are split as separate chunks."""
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker = TypeScriptASTChunker()
        
        code = '''
class MyClass {
    method(): void {}
}

class OtherClass {
    other(): void {}
}
'''
        chunks = chunker.chunk(code)
        
        # Should have classes and methods
        assert len(chunks) >= 2
        class_chunks = [c for c in chunks if c.metadata.get("node_type") == "class_declaration"]
        assert len(class_chunks) >= 2

    def test_extracts_function_name(self):
        """TC-2.2.2: Function name is extracted in metadata."""
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker = TypeScriptASTChunker()
        
        code = '''
function myFunction(): string {
    return "hello";
}
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 1
        assert chunks[0].metadata["name"] == "myFunction"
        assert chunks[0].metadata["node_type"] == "function_declaration"

    def test_splits_methods(self):
        """TC-2.2.2: Methods are split as separate chunks."""
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker = TypeScriptASTChunker()
        
        code = '''
class Service {
    method1(): void {}
    method2(): void {}
}
'''
        chunks = chunker.chunk(code)
        
        # Should have class and methods
        method_chunks = [c for c in chunks if c.metadata.get("node_type") == "method_definition"]
        assert len(method_chunks) >= 2

    def test_supports_language_check(self):
        """TypeScriptASTChunker supports typescript, ts, tsx languages."""
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker = TypeScriptASTChunker()
        
        assert chunker.supports_language("typescript") is True
        assert chunker.supports_language("ts") is True
        assert chunker.supports_language("tsx") is True
        assert chunker.supports_language("python") is False

    def test_empty_code_returns_empty_list(self):
        """Empty code returns empty list."""
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker = TypeScriptASTChunker()
        chunks = chunker.chunk("")
        
        assert chunks == []


class TestGoASTChunker:
    """TC-2.2.3: GoASTChunker 按函数/方法/类型切分"""

    def test_splits_functions(self):
        """TC-2.2.3: Functions are split as separate chunks."""
        from chunkers.go_ast import GoASTChunker
        
        chunker = GoASTChunker()
        
        code = '''package main

func hello() {
    fmt.Println("Hello")
}

func world() {
    fmt.Println("World")
}
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 2
        assert "func hello()" in chunks[0].text
        assert "func world()" in chunks[1].text

    def test_splits_methods(self):
        """TC-2.2.3: Methods are split as separate chunks."""
        from chunkers.go_ast import GoASTChunker
        
        chunker = GoASTChunker()
        
        code = '''package main

type Service struct{}

func (s *Service) Method1() {}

func (s *Service) Method2() {}
'''
        chunks = chunker.chunk(code)
        
        # Should have type and methods
        assert len(chunks) >= 3
        method_chunks = [c for c in chunks if c.metadata.get("node_type") == "method_declaration"]
        assert len(method_chunks) >= 2

    def test_splits_types(self):
        """TC-2.2.3: Type declarations are split as separate chunks."""
        from chunkers.go_ast import GoASTChunker
        
        chunker = GoASTChunker()
        
        code = '''package main

type MyStruct struct {
    Field string
}

type MyInterface interface {
    Method()
}
'''
        chunks = chunker.chunk(code)
        
        # Should have type declarations
        type_chunks = [c for c in chunks if c.metadata.get("node_type") == "type_declaration"]
        assert len(type_chunks) >= 2

    def test_extracts_function_name(self):
        """TC-2.2.3: Function name is extracted in metadata."""
        from chunkers.go_ast import GoASTChunker
        
        chunker = GoASTChunker()
        
        code = '''package main

func myFunction() string {
    return "hello"
}
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 1
        assert chunks[0].metadata["name"] == "myFunction"
        assert chunks[0].metadata["node_type"] == "function_declaration"

    def test_supports_language_check(self):
        """GoASTChunker supports go and golang languages."""
        from chunkers.go_ast import GoASTChunker
        
        chunker = GoASTChunker()
        
        assert chunker.supports_language("go") is True
        assert chunker.supports_language("golang") is True
        assert chunker.supports_language("GO") is True  # case-insensitive
        assert chunker.supports_language("python") is False

    def test_empty_code_returns_empty_list(self):
        """Empty code returns empty list."""
        from chunkers.go_ast import GoASTChunker
        
        chunker = GoASTChunker()
        chunks = chunker.chunk("")
        
        assert chunks == []


class TestASTChunkerRegistry:
    """TC-2.2.4: AST chunkers 注册到 ChunkerRegistry"""

    def test_python_ast_registered(self):
        """TC-2.2.4: PythonASTChunker is registered."""
        from chunkers.registry import registry
        
        assert registry.is_registered("python-ast")

    def test_typescript_ast_registered(self):
        """TC-2.2.4: TypeScriptASTChunker is registered."""
        from chunkers.registry import registry
        
        assert registry.is_registered("typescript-ast")

    def test_go_ast_registered(self):
        """TC-2.2.4: GoASTChunker is registered."""
        from chunkers.registry import registry
        
        assert registry.is_registered("go-ast")

    def test_get_for_language_python(self):
        """TC-2.2.4: get_for_language returns PythonASTChunker for python."""
        from chunkers.registry import registry
        from chunkers.python_ast import PythonASTChunker
        
        chunker_cls = registry.get_for_language("python")
        assert chunker_cls == PythonASTChunker

    def test_get_for_language_typescript(self):
        """TC-2.2.4: get_for_language returns TypeScriptASTChunker for typescript."""
        from chunkers.registry import registry
        from chunkers.typescript_ast import TypeScriptASTChunker
        
        chunker_cls = registry.get_for_language("typescript")
        assert chunker_cls == TypeScriptASTChunker

    def test_get_for_language_go(self):
        """TC-2.2.4: get_for_language returns GoASTChunker for go."""
        from chunkers.registry import registry
        from chunkers.go_ast import GoASTChunker
        
        chunker_cls = registry.get_for_language("go")
        assert chunker_cls == GoASTChunker

    def test_list_chunkers_includes_ast(self):
        """TC-2.2.4: list_chunkers includes AST chunkers."""
        from chunkers.registry import registry
        
        chunkers = registry.list_chunkers()
        
        assert "python-ast" in chunkers
        assert "typescript-ast" in chunkers
        assert "go-ast" in chunkers


class TestASTChunkerBase:
    """Tests for ASTChunkerBase functionality."""

    def test_is_tree_sitter_available(self):
        """is_tree_sitter_available returns True when tree-sitter is installed."""
        from chunkers.ast_base import ASTChunkerBase
        
        assert ASTChunkerBase.is_tree_sitter_available() is True

    def test_metadata_passed_to_chunks(self):
        """Base metadata is passed to chunks."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
def hello():
    pass
'''
        chunks = chunker.chunk(code, metadata={"source": "test.py"})
        
        assert len(chunks) == 1
        assert chunks[0].metadata["source"] == "test.py"
        assert chunks[0].metadata["name"] == "hello"

    def test_chunk_index_increments(self):
        """chunk_index increments correctly."""
        from chunkers.python_ast import PythonASTChunker
        
        chunker = PythonASTChunker()
        
        code = '''
def func1():
    pass

def func2():
    pass

def func3():
    pass
'''
        chunks = chunker.chunk(code)
        
        assert len(chunks) == 3
        assert chunks[0].metadata["chunk_index"] == 0
        assert chunks[1].metadata["chunk_index"] == 1
        assert chunks[2].metadata["chunk_index"] == 2


class TestExistingChunkersStillWork:
    """Ensure existing chunkers still work after AST additions."""

    def test_simple_chunker_works(self):
        """SimpleChunker still works."""
        from chunkers.simple import SimpleChunker
        
        chunker = SimpleChunker(chunk_size=10, overlap=0)
        text = "a" * 25
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 3

    def test_markdown_chunker_works(self):
        """MarkdownChunker still works."""
        from chunkers.markdown import MarkdownChunker
        
        chunker = MarkdownChunker(chunk_size=500)
        text = "# Title\n\nContent.\n\n## Section\n\nMore content."
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 2

    def test_line_chunker_works(self):
        """LineChunker still works."""
        from chunkers.line import LineChunker
        
        chunker = LineChunker(chunk_size=2, overlap=0)
        text = "Line 1\nLine 2\nLine 3"
        chunks = chunker.chunk(text)
        
        assert len(chunks) == 2

    def test_registry_still_has_builtin_chunkers(self):
        """Registry still has all built-in chunkers."""
        from chunkers.registry import registry
        
        assert registry.is_registered("simple")
        assert registry.is_registered("line")
        assert registry.is_registered("markdown")