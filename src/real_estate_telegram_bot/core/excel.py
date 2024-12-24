import openpyxl
from openpyxl.styles import Alignment, PatternFill
from openpyxl.utils import get_column_letter


def format_areas(filepath: str, header_color: str = "92d050"):
    # Load the Excel file to apply formatting
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active

    # Set the alignment to center for all cells
    for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
        for cell in row:
            cell.alignment = Alignment(horizontal='center', vertical='center')

    # Apply green background to the header row
    header_fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")
    for cell in ws[1]:
        cell.fill = header_fill

    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter  # Get the column letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2)  # Add extra padding
        ws.column_dimensions[column].width = adjusted_width

    # Save the formatted Excel file
    wb.save(filepath)
    return filepath


def format_service_charge(filepath: str, master_project_en: str, header_color: str = "92d050"):
    """
    Formats an Excel file by adding specific headers and applying styles.

    Parameters:
    - filepath (str): Path to the Excel file to format.
    - b1_value (str): Value to write in cell B1.
    - header_color (str): Hex color code for the header background. Default is "92d050".

    Returns:
    - str: The filepath of the formatted Excel file.
    """
    # Load the Excel workbook and select the active worksheet
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active

    # 1. Insert two new rows at the top to make space for headers
    ws.insert_rows(1, amount=2)

    # 2. Write "master_project_en" in cell A1
    ws['A1'] = "master_project_en"
    
    # Make it bold
    ws['A1'].font = openpyxl.styles.Font(bold=True)

    # 3. Write the provided b1_value in cell B1
    ws['B1'] = master_project_en

    # 4. Write "Service charges (AED per sqft/year)" across cells D2 to H2
    # Merge cells D2 to H2 for a unified header
    ws.merge_cells('C2:G2')
    ws['C2'] = "Service charges (AED per sqft/year)"
    
    # Make it bold
    ws['C2'].font = openpyxl.styles.Font(bold=True)

    # Center the merged cell both horizontally and vertically
    ws['C2'].alignment = Alignment(horizontal='center', vertical='center')

    # 5. Ensure that the table data starts from the 3rd row
    # (Already handled by inserting two new rows)

    # # Set the alignment to left for all cells
    # for row in ws.iter_rows(min_row=1, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
    #     for cell in row:
    #         cell.alignment = Alignment(horizontal='left', vertical='left')

    # Apply background color to specific header rows
    # Apply header_color to A1, B1, and the merged D2:H2
    header_fill = PatternFill(start_color=header_color, end_color=header_color, fill_type="solid")

    ws['A1'].fill = header_fill
    for cell in ["A3", "B3", "C3", "D3", "E3", "F3", "G3"]:
        ws[cell].fill = header_fill

    # If there are other headers in row 2 (apart from D2:H2), apply the fill as well
    # Example: If C2 exists and is part of headers
    # for cell in ws[2]:
    #     if cell.coordinate not in ['D2', 'E2', 'F2', 'G2', 'H2']:
    #         cell.fill = header_fill

    # Auto-adjust column widths based on the maximum length in each column
    for col in [ws[get_column_letter(i)] for i in range(1, 2+1)]:
        max_length = 0
        column = col[0].column_letter  # Get the column letter
        for cell in col:
            try:
                cell_value = str(cell.value) if cell.value else ""
                cell_length = len(cell_value)
                if cell_length > max_length:
                    max_length = cell_length
            except:
                pass
        adjusted_width = max_length + 2  # Add extra padding
        ws.column_dimensions[column].width = adjusted_width

    # Save the formatted Excel file
    wb.save(filepath)
    return filepath
