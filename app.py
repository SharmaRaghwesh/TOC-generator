import streamlit as st
import tempfile
import os
from main_extractor import BidderDocumentExtractor
from merge_utils import (
    get_pdf_info,
    create_simple_toc,
    merge_all_pdfs,
    combine_toc_and_merged,
    print_summary
)

st.set_page_config(page_title="Bidder PDF Merger", layout="wide")

st.title("📄 Bidder Document Extractor ,Merger and TOC Generator")

# --- Input Section ---
brief_note_pdf = st.file_uploader("1️⃣ Upload Brief Note PDF", type="pdf")
supporting_docs = st.file_uploader("2️⃣ Upload All Supporting PDFs", type="pdf", accept_multiple_files=True)
bidder_name = st.text_input("3️⃣ Enter Bidder Name to Match")

if st.button("🚀 Process"):
    if not brief_note_pdf or not supporting_docs or not bidder_name:
        st.warning("Please provide all three inputs!")
        st.stop()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded brief note
        brief_note_path = os.path.join(tmpdir, "brief_note.pdf")
        with open(brief_note_path, "wb") as f:
            f.write(brief_note_pdf.read())

        # Run extraction
        extractor = BidderDocumentExtractor(brief_note_path)
        matched_docs = extractor.get_documents_for_bidder(bidder_name)
        bidder_file_name = []
        # print(f"\nFound {len(documents)} documents for {bidder_name}:")
        for i, doc in enumerate(matched_docs, 1):
            print(f"{i}. {doc}")
            bidder_file_name.append(doc)
        bidder_file_name.insert(0, "00.pdf")

        if not matched_docs:
            st.error("No documents matched the bidder name.")
            st.stop()

        # Save uploaded supporting docs
        input_folder = os.path.join(tmpdir, "docs")
        os.makedirs(input_folder, exist_ok=True)
        uploaded_files_dict = {}
        for file in supporting_docs:
            file_path = os.path.join(input_folder, file.name)
            with open(file_path, "wb") as f:
                f.write(file.read())
            uploaded_files_dict[file.name] = file_path

        # Ensure the matched docs exist in uploaded files
        available_files = set(uploaded_files_dict.keys())
        final_files = ["00.pdf"] + [f for f in matched_docs if f in available_files]

        if not final_files:
            st.error("None of the matched files were found in the uploaded documents.")
            st.stop()

        # Create dummy 00.pdf (or replace with an actual front page if needed)
        with open(os.path.join(input_folder, "00.pdf"), "wb") as f:
            f.write(b" ")

        output_folder = os.path.join(tmpdir, "output")
        os.makedirs(output_folder, exist_ok=True)

        # Paths
        toc_path = os.path.join(output_folder, "toc.pdf")
        merged_path = os.path.join(output_folder, "merged.pdf")
        final_path = os.path.join(output_folder, "final_output.pdf")

        # Merge steps
        # pdf_info = get_pdf_info(input_folder, final_files)
        pdf_info = get_pdf_info(input_folder, bidder_file_name)
        create_simple_toc(pdf_info, toc_path)
        merge_all_pdfs(input_folder, final_files, merged_path)
        combine_toc_and_merged(toc_path, merged_path, final_path)

        # Download buttons
        st.success("✅ Merging Completed!")
        with open(final_path, "rb") as f:
            st.download_button("📅 Download Final Merged PDF", f, file_name="Final_Merged_Document.pdf")

        with open(toc_path, "rb") as f:
            st.download_button("📅 Download Table of Contents", f, file_name="Table_of_Contents.pdf")
