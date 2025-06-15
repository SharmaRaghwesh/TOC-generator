import re
import os
import warnings
import logging
from pypdf import PdfWriter, PdfReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Suppress pypdf warnings (optional)
logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf")


def sort_key(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group()) if match else float('inf')

def get_pdf_info(input_folder, sorted_files):
    """Get basic info about each PDF: name, page count, and placement in merged doc"""
    pdf_info = []
    page_counter = 1

    print("\n📊 Analyzing PDFs:")
    for filename in sorted_files:
        full_path = os.path.join(input_folder, filename)
        print(f"📄 Analyzing: {filename}")

        try:
            reader = PdfReader(full_path)
            page_count = len(reader.pages)

            # Clean up filename for display
            display_name = filename.replace('.pdf', '').replace('_', ' ').title()

            # Calculate page range in merged document
            start_page = page_counter
            end_page = page_counter + page_count - 1

            pdf_info.append({
                'filename': filename,
                'display_name': display_name,
                'page_count': page_count,
                'start_page': start_page,
                'end_page': end_page
            })

            page_counter += page_count
            print(f"   ✅ {page_count} pages, will be placed at pages {start_page}-{end_page}")

        except Exception as e:
            print(f"   ❌ Error reading {filename}: {e}")
            continue

    return pdf_info

def create_simple_toc(pdf_info, toc_path):
    """Create a simple 3-column TOC: Name | No. of Pages | Placed At"""
    c = canvas.Canvas(toc_path, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width/2, height - 60, "Table of Contents")

    # Draw line under title
    c.line(50, height - 80, width - 50, height - 80)

    # Column headers
    c.setFont("Helvetica-Bold", 12)
    y = height - 120

    # Column positions
    col1_x = 60    # Name
    col2_x = 350   # No. of Pages
    col3_x = 450   # Placed At

    # Draw headers
    c.drawString(col1_x, y, "Document Name")
    c.drawString(col2_x, y, "Pages")
    c.drawString(col3_x, y, "Location")

    # Draw line under headers
    c.line(50, y - 10, width - 50, y - 10)

    # Content
    c.setFont("Helvetica", 11)
    y -= 35

    for i, info in enumerate(pdf_info, 1):
        # Document name (truncate if too long)
        name = info['display_name']
        if len(name) > 35:
            name = name[:32] + "..."

        # Draw row
        c.drawString(col1_x, y, f"{i}. {name}")
        c.drawString(col2_x, y, str(info['page_count']))

        # Page range
        if info['start_page'] == info['end_page']:
            page_range = str(info['start_page'])
        else:
            page_range = f"{info['start_page']}-{info['end_page']}"
        c.drawString(col3_x, y, page_range)

        # Original filename in smaller text
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawString(col1_x + 20, y - 12, info['filename'])
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 11)

        y -= 30

        # New page if needed
        if y < 100:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 50

    # Add footer note
    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, 50, "Note: This TOC is page 0. Merged content starts from page 1.")

    c.save()

def merge_all_pdfs(input_folder, sorted_files, output_path):
    """Merge all PDFs into one document"""
    writer = PdfWriter()

    print("\n🔗 Merging PDFs:")
    for filename in sorted_files:
        try:
            file_path = os.path.join(input_folder, filename)
            reader = PdfReader(file_path)

            # Add all pages from this PDF
            for page in reader.pages:
                writer.add_page(page)
            print(f"   ✅ Added: {filename}")

        except Exception as e:
            print(f"   ❌ Error adding {filename}: {e}")
            continue

    # Write the merged PDF
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)

    print(f"   📄 Merged PDF saved to: {output_path}")

def combine_toc_and_merged(toc_path, merged_path, final_path):
    """Combine TOC (as page 0) with merged PDF (starting from page 1)"""
    writer = PdfWriter()

    try:
        print("\n📖 Creating final PDF with TOC...")

        # Add TOC first (this becomes page 0)
        toc_reader = PdfReader(toc_path)
        for page in toc_reader.pages:
            writer.add_page(page)
        print("   ✅ Added TOC (Page 0)")

        # Add merged content (starts from page 1)
        merged_reader = PdfReader(merged_path)
        for page in merged_reader.pages:
            writer.add_page(page)
        print("   ✅ Added merged content (Pages 1+)")

        # Save final PDF
        with open(final_path, 'wb') as output_file:
            writer.write(output_file)

        print(f"   📚 Final PDF saved to: {final_path}")

    except Exception as e:
        print(f"   ❌ Error creating final PDF: {e}")

def print_summary(pdf_info):
    """Print a summary of what will be merged"""
    print("\n📋 Merge Summary:")
    print("-" * 60)
    print(f"{'No.':<4} {'Document':<25} {'No of Pages':<8} {'Place At':<12}")
    print("-" * 60)

    total_pages = 0
    for i, info in enumerate(pdf_info, 1):
        name = info['display_name'][:22] + "..." if len(info['display_name']) > 25 else info['display_name']
        location = f"{info['start_page']}-{info['end_page']}" if info['start_page'] != info['end_page'] else str(info['start_page'])

        print(f"{i:<4} {name:<25} {info['page_count']:<8} {location:<12}")
        total_pages += info['page_count']

    print("-" * 60)
    print(f"Total: {len(pdf_info)} documents, {total_pages} pages")
    print("TOC will be page 0, content starts from page 1")

def main():
    # Check if input folder exists
    if not os.path.exists(INPUT_FOLDER):
        print(f"❌ Input folder '{INPUT_FOLDER}' not found!")
        return

    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    # Get PDF files
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith('.pdf') and not f.startswith('.')]

    if not files:
        print(f"❌ No PDF files found in '{INPUT_FOLDER}'!")
        return

    print(f"📁 Found {len(files)} PDF files")

    # Sort files
    # sorted_files = sorted(files, key=sort_key)
    sorted_files = bidder_file_name.copy()
    bidder_file_name
    print(f"📝 Processing order: {', '.join(sorted_files)}")

    # Get PDF information
    pdf_info = get_pdf_info(INPUT_FOLDER, sorted_files)

    if not pdf_info:
        print("❌ No valid PDFs could be processed!")
        return

    # Print summary
    print_summary(pdf_info)

    # Define paths
    toc_path = os.path.join(OUTPUT_FOLDER, TOC_FILENAME)
    merged_path = os.path.join(OUTPUT_FOLDER, 'temp_merged.pdf')
    final_path = os.path.join(OUTPUT_FOLDER, MERGED_FILENAME)

    # Step 1: Create TOC
    print(f"\n📋 Creating Table of Contents...")
    create_simple_toc(pdf_info, toc_path)
    print(f"   ✅ TOC saved to: {toc_path}")

    # Step 2: Merge all PDFs
    merge_all_pdfs(INPUT_FOLDER, sorted_files, merged_path)

    # Step 3: Combine TOC + Merged PDF
    combine_toc_and_merged(toc_path, merged_path, final_path)

    # Clean up temporary file
    try:
        os.remove(merged_path)
        print("🧹 Cleaned up temporary files")
    except:
        pass

    print(f"\n🎉 SUCCESS! Final PDF created: {final_path}")
    print(f"📄 TOC is page 0, content starts from page 1")

if __name__ == "__main__":
    main()
