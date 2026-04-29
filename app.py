import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO


st.set_page_config(
    page_title="PDF to Excel Converter",
    page_icon="📄",
    layout="centered"
)

st.title("📄 PDF to Excel Converter")
st.write("Upload a PDF file. This app will extract tables and convert them into an Excel file.")


def clean_table(table):
    cleaned_rows = []

    for row in table:
        if row is None:
            continue

        cleaned_row = []

        for cell in row:
            if cell is None:
                cleaned_row.append("")
            else:
                cleaned_row.append(str(cell).strip())

        if any(cell != "" for cell in cleaned_row):
            cleaned_rows.append(cleaned_row)

    return cleaned_rows


def convert_pdf_to_excel(uploaded_file):
    output = BytesIO()
    tables_found = 0

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        with pdfplumber.open(uploaded_file) as pdf:

            for page_number, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()

                if tables:
                    for table_number, table in enumerate(tables, start=1):
                        cleaned_table = clean_table(table)

                        if len(cleaned_table) == 0:
                            continue

                        df = pd.DataFrame(cleaned_table)

                        sheet_name = f"Page{page_number}_Table{table_number}"
                        sheet_name = sheet_name[:31]

                        df.to_excel(
                            writer,
                            sheet_name=sheet_name,
                            index=False,
                            header=False
                        )

                        tables_found += 1

        if tables_found == 0:
            df = pd.DataFrame({
                "Message": [
                    "No tables were found in this PDF.",
                    "This may be a scanned PDF or the table structure may not be clear."
                ]
            })
            df.to_excel(writer, sheet_name="No_Tables_Found", index=False)

    output.seek(0)
    return output, tables_found


uploaded_pdf = st.file_uploader("Upload your PDF file", type=["pdf"])

if uploaded_pdf is not None:
    st.success("PDF uploaded successfully!")

    if st.button("Convert PDF to Excel"):
        with st.spinner("Converting PDF to Excel..."):
            excel_file, total_tables = convert_pdf_to_excel(uploaded_pdf)

        if total_tables > 0:
            st.success(f"Conversion completed! {total_tables} table(s) found.")
        else:
            st.warning("No tables were found in this PDF.")

        st.download_button(
            label="⬇️ Download Excel File",
            data=excel_file,
            file_name="converted_pdf_tables.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )


st.markdown("---")
st.info(
    "Note: This app works best with normal text-based PDFs. "
    "If your PDF is scanned like an image, OCR will be needed."
)