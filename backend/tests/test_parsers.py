import tempfile
from pathlib import Path
import pytest
from app.parsers.factory import get_parser_for_file
from app.parsers.tabular_parser import TabularParser
from app.parsers.text_parser import TextParser

@pytest.mark.asyncio
async def test_text_parser():
    with tempfile.NamedTemporaryFile("w+", suffix=".txt", delete=False) as f:
        f.write("Line 1: AuraChat test\nLine 2: Multi-turn document analysis\n")
        f.flush()
        temp_path = Path(f.name)
        
    try:
        parser = get_parser_for_file("sample.txt")
        assert isinstance(parser, TextParser)
        parsed = await parser.parse(temp_path, "sample.txt")
        assert "AuraChat test" in parsed.text_content
        assert parsed.token_estimate > 0
        assert parsed.file_type == "txt"
    finally:
        if temp_path.exists():
            temp_path.unlink()

@pytest.mark.asyncio
async def test_csv_parser():
    with tempfile.NamedTemporaryFile("w+", suffix=".csv", delete=False) as f:
        f.write("name,age,city\nAlice,30,Seattle\nBob,25,Boston\n")
        f.flush()
        temp_path = Path(f.name)
        
    try:
        parser = get_parser_for_file("data.csv")
        assert isinstance(parser, TabularParser)
        parsed = await parser.parse(temp_path, "data.csv")
        assert "Alice" in parsed.text_content
        assert "Dimensions: 2 rows" in parsed.text_content
        assert parsed.file_type == "csv"
    finally:
        if temp_path.exists():
            temp_path.unlink()
