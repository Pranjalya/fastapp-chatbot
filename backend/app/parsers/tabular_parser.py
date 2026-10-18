from pathlib import Path
import pandas as pd
from app.parsers.base import BaseParser, ParsedDocument

def df_to_markdown_safe(df: pd.DataFrame, index: bool = False) -> str:
    """Render DataFrame to markdown table with fallback to plain string."""
    try:
        return df.to_markdown(index=index) or str(df)
    except Exception:
        return df.to_string(index=index)

class TabularParser(BaseParser):
    async def parse(self, file_path: Path, filename: str) -> ParsedDocument:
        ext = file_path.suffix.lower()
        
        if ext in [".xlsx", ".xls"]:
            excel_file = pd.ExcelFile(str(file_path))
            sheet_names = excel_file.sheet_names
            parts = [f"# Excel Workbook: {filename} (Sheets: {', '.join(sheet_names)})\n"]
            total_rows = 0
            
            for sheet in sheet_names[:5]:  # limit to first 5 sheets
                df = pd.read_excel(excel_file, sheet_name=sheet)
                total_rows += len(df)
                parts.append(f"## Sheet: {sheet}")
                parts.append(f"Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
                parts.append(f"Columns: {', '.join([str(c) for c in df.columns])}")
                parts.append("\nSample Data (First 5 Rows):")
                parts.append(df_to_markdown_safe(df.head(5), index=False))
                parts.append("\n" + "=" * 40 + "\n")
            
            content = "\n".join(parts)
            summary = f"Excel spreadsheet with {len(sheet_names)} sheets and {total_rows} total rows."
        else:
            # CSV or TSV
            sep = "\t" if ext == ".tsv" else ","
            try:
                df = pd.read_csv(str(file_path), sep=sep)
            except Exception:
                df = pd.read_csv(str(file_path), sep=sep, encoding="latin1")
            
            cols = list(df.columns)
            row_count, col_count = df.shape
            
            parts = [
                f"# Tabular Data: {filename}",
                f"Dimensions: {row_count} rows × {col_count} columns",
                f"Columns & Types: {', '.join([f'{col} ({df[col].dtype})' for col in cols])}",
                "\n### First 5 Sample Rows:",
                df_to_markdown_safe(df.head(5), index=False),
            ]
            
            # Add summary stats for numeric columns if available
            numeric_desc = df.describe()
            if not numeric_desc.empty and numeric_desc.shape[1] > 0:
                parts.append("\n### Numeric Statistics Overview:")
                parts.append(df_to_markdown_safe(numeric_desc, index=True))
                
            content = "\n".join(parts)
            summary = f"Tabular dataset ({row_count} rows, {col_count} columns). Columns: {', '.join([str(c) for c in cols[:8]])}"
        
        token_estimate = max(1, len(content) // 4)
        
        return ParsedDocument(
            filename=filename,
            file_type=ext.lstrip("."),
            text_content=content,
            token_estimate=token_estimate,
            summary_or_toc=summary,
            metadata={"shape": list(df.shape) if 'df' in locals() else []}
        )
