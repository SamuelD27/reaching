"""
Export Manager for Multiple Output Formats
Supports XLSX, CSV, and JSON exports
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging


logger = logging.getLogger(__name__)


class ExportManager:
    """
    Manage exports to multiple formats

    Supported formats:
    - xlsx: Excel format (default)
    - csv: Comma-separated values
    - json: JSON format
    """

    def __init__(self, output_dir: str = "./output", timestamp_filenames: bool = True):
        """
        Initialize export manager

        Args:
            output_dir: Directory for output files
            timestamp_filenames: Add timestamp to filenames
        """
        self.output_dir = Path(output_dir)
        self.timestamp_filenames = timestamp_filenames

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, base_name: str, format: str) -> Path:
        """
        Generate filename with optional timestamp

        Args:
            base_name: Base filename without extension
            format: File format (xlsx, csv, json)

        Returns:
            Path object for the file
        """
        if self.timestamp_filenames:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{base_name}_{timestamp}.{format}"
        else:
            filename = f"{base_name}.{format}"

        return self.output_dir / filename

    def export(self, data: List[Dict[str, Any]], base_name: str,
               format: str = 'xlsx') -> Path:
        """
        Export data to specified format

        Args:
            data: List of dictionaries to export
            base_name: Base filename (without extension)
            format: Output format ('xlsx', 'csv', or 'json')

        Returns:
            Path to the exported file

        Raises:
            ValueError: If format is not supported
        """
        format = format.lower()

        if format not in ['xlsx', 'csv', 'json']:
            raise ValueError(f"Unsupported format: {format}. Use 'xlsx', 'csv', or 'json'")

        if not data:
            logger.warning("No data to export")
            return None

        filepath = self._get_filename(base_name, format)

        try:
            if format == 'xlsx':
                self._export_xlsx(data, filepath)
            elif format == 'csv':
                self._export_csv(data, filepath)
            elif format == 'json':
                self._export_json(data, filepath)

            logger.info(f"✅ Exported {len(data)} records to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            raise

    def _export_xlsx(self, data: List[Dict], filepath: Path) -> None:
        """Export to Excel format"""
        df = pd.DataFrame(data)

        # Write to Excel with auto-width columns
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Contacts')

            # Auto-adjust column widths
            worksheet = writer.sheets['Contacts']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).apply(len).max(),
                    len(col)
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)

    def _export_csv(self, data: List[Dict], filepath: Path) -> None:
        """Export to CSV format"""
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False, encoding='utf-8')

    def _export_json(self, data: List[Dict], filepath: Path) -> None:
        """Export to JSON format"""
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'total_records': len(data)
            },
            'contacts': data
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

    def export_multiple_formats(self, data: List[Dict], base_name: str,
                                formats: List[str] = None) -> Dict[str, Path]:
        """
        Export to multiple formats at once

        Args:
            data: List of dictionaries to export
            base_name: Base filename
            formats: List of formats (default: ['xlsx', 'csv', 'json'])

        Returns:
            Dict mapping format to filepath
        """
        formats = formats or ['xlsx', 'csv', 'json']
        results = {}

        for format in formats:
            try:
                filepath = self.export(data, base_name, format)
                results[format] = filepath
            except Exception as e:
                logger.error(f"Failed to export {format}: {e}")
                results[format] = None

        return results

    def export_with_stats(self, data: List[Dict], base_name: str,
                         stats: Dict[str, Any] = None,
                         format: str = 'xlsx') -> Path:
        """
        Export data with statistics sheet (XLSX only)

        Args:
            data: Contact data
            base_name: Base filename
            stats: Statistics dictionary
            format: Output format

        Returns:
            Path to exported file
        """
        if format != 'xlsx' or not stats:
            return self.export(data, base_name, format)

        filepath = self._get_filename(base_name, format)

        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Write contacts
                df_contacts = pd.DataFrame(data)
                df_contacts.to_excel(writer, index=False, sheet_name='Contacts')

                # Write statistics
                stats_data = []
                for key, value in stats.items():
                    stats_data.append({'Metric': key, 'Value': value})

                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, index=False, sheet_name='Statistics')

            logger.info(f"✅ Exported {len(data)} records with stats to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Export with stats failed: {e}")
            raise


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create export manager
    manager = ExportManager(output_dir="./output", timestamp_filenames=True)

    # Sample data
    sample_contacts = [
        {
            'name': 'John Smith',
            'company': 'Goldman Sachs',
            'title': 'Managing Director',
            'email': 'john.smith@gs.com',
            'location': 'Singapore'
        },
        {
            'name': 'Jane Doe',
            'company': 'Morgan Stanley',
            'title': 'Vice President',
            'email': 'jane.doe@morganstanley.com',
            'location': 'Hong Kong'
        }
    ]

    print("Testing export manager...\n")

    # Export to single format
    print("1. Exporting to XLSX...")
    xlsx_file = manager.export(sample_contacts, 'test_contacts', format='xlsx')
    print(f"   Created: {xlsx_file}\n")

    # Export to multiple formats
    print("2. Exporting to multiple formats...")
    results = manager.export_multiple_formats(sample_contacts, 'multi_format_test')
    for format, filepath in results.items():
        print(f"   {format.upper()}: {filepath}")

    # Export with statistics
    print("\n3. Exporting with statistics...")
    stats = {
        'Total Contacts': 2,
        'Companies': 2,
        'Locations': 2,
        'Extracted At': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    stats_file = manager.export_with_stats(sample_contacts, 'contacts_with_stats', stats=stats)
    print(f"   Created: {stats_file}")

    print("\n✅ Export tests complete!")
