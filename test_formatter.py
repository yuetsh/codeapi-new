import pytest

from formatter import FormatError, format_code


def test_format_python_normalizes_spacing():
    result = format_code("x=1\n", "python")
    assert result == "x = 1\n"


def test_format_turtle_uses_python_formatter():
    result = format_code("t=1\n", "turtle")
    assert result == "t = 1\n"


def test_format_python_syntax_error_raises():
    with pytest.raises(FormatError):
        format_code("def foo(:\n", "python")


def test_format_c_uses_allman_braces():
    result = format_code("int main(){int x=1;return x;}", "c")
    assert result.rstrip("\n") == "int main()\n{\n    int x = 1;\n    return x;\n}"


def test_format_cpp_uses_allman_braces():
    result = format_code("class Foo{};", "cpp")
    assert result.rstrip("\n") == "class Foo\n{\n};"


def test_format_unsupported_language_raises():
    with pytest.raises(FormatError):
        format_code("print(1)", "java")
