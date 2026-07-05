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


def test_format_sql_uppercases_keywords():
    result = format_code("select * from students where score>60", "sql")
    assert result == "SELECT * FROM students WHERE score>60"


def test_format_sql_splits_multiple_statements():
    result = format_code(
        "delete from students where score<60;insert into students (id) values (9);",
        "sql",
    )
    assert result == (
        "DELETE FROM students WHERE score<60;\n\n"
        "INSERT INTO students (id) VALUES (9);"
    )


def test_format_sql_tolerates_syntax_errors():
    result = format_code("select from where", "sql")
    assert result == "SELECT FROM WHERE"
