# TOC-generator
# 🧾 Bidder PDF Merger App

This Streamlit application allows users to:
- Upload a *brief note* PDF containing a list of documents for multiple bidders.
- Upload all relevant individual documents.
- Enter a bidder name to extract the documents related to that bidder.
- Automatically generate a merged PDF and a Table of Contents (TOC) page.

## 🚀 Features

- Extracts document list using intelligent parsing from the brief note.
- Matches document names with uploaded files.
- Merges documents in the correct order.
- Generates a professional TOC page.
- Allows users to download the final PDF (TOC + Merged Documents).

## 📁 File Structure

```bash
.
├── app.py                 # Main Streamlit app
├── extractor.py          # Contains BidderDocumentExtractor logic
├── merge_utils.py        # Functions for merging, TOC creation, etc.
├── requirements.txt      # Required Python libraries
└── README.md             # This file
