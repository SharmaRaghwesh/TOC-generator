import PyPDF2
import re
from collections import defaultdict
from typing import Dict, List
import pdfplumber

class BidderDocumentExtractor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.bidder_documents = defaultdict(list)
        self.raw_text = ""

    def extract_text_from_pdf(self) -> str:
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                if text.strip():
                    self.raw_text = text
                    return text

            # Fallback to PyPDF2 if pdfplumber fails
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                self.raw_text = text
                return text

        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def parse_bidder_documents(self) -> Dict[str, List[str]]:
        if not self.raw_text:
            self.extract_text_from_pdf()

        lines = self.raw_text.split('\n')
        current_bidder = None
        in_table_section = False

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                continue

            # Detect bidder name
            bidder_match = re.match(
                r'^[A-Z][A-Z\s&\.]+(?:PAINTS|LIMITED|PRIVATE|INDUSTRY|TILES|ENTERPRISES|CONSTRUCTION|SOCIETY|COOPERATIVE|DEVELOPERS|ENGINEERS|ENGINEERING|COMPANY)?-[A-Z]+$', line
            )
            if bidder_match:
                current_bidder = line
                in_table_section = False
                # print(f"\nFound bidder: {current_bidder}")
                # print("Next lines:")
                for j in range(1, 10):
                    if i + j < len(lines):
                        print(f"  {j}: {lines[i + j]}")
                continue

            # Detect flexible table header
            if current_bidder and any(
                keyword in line.lower() for keyword in ['file name', 's.no', 'description', 'context', 'placed']
            ):
                in_table_section = True
                print(f"Detected table header for {current_bidder}")
                continue

            # Extract document names in table
            if current_bidder and in_table_section:
                if re.match(r'^\d+\s+', line):
                    parts = line.split()
                    filename = None
                    for j in range(1, len(parts)):
                        candidate = ' '.join(parts[1:j + 1])
                        if '.' in candidate and candidate.lower().endswith(('.pdf', '.doc', '.docx')):
                            filename = candidate
                            break
                    if filename:
                        self.bidder_documents[current_bidder].append(filename)
                        print(f"→ Added document from row: {filename}")
                    continue

                # Extract directly from line if it contains a PDF
                pdf_match = re.search(r'(\S+\.pdf)', line, re.IGNORECASE)
                if pdf_match:
                    filename = pdf_match.group(1)
                    if filename not in self.bidder_documents[current_bidder]:
                        self.bidder_documents[current_bidder].append(filename)
                        print(f"→ Added document from inline PDF match: {filename}")
                    continue

            # Fallback: Look ahead for PDFs near a bidder if no table detected
            if current_bidder and not in_table_section:
                for lookahead in range(1, 20):
                    if i + lookahead < len(lines):
                        doc_line = lines[i + lookahead].strip()
                        pdf_match = re.search(r'(\S+\.pdf)', doc_line, re.IGNORECASE)
                        if pdf_match:
                            filename = pdf_match.group(1)
                            if filename not in self.bidder_documents[current_bidder]:
                                self.bidder_documents[current_bidder].append(filename)
                                print(f"→ Fallback: Added document for {current_bidder}: {filename}")
                    else:
                        break

        return dict(self.bidder_documents)

    def get_documents_for_bidder(self, bidder_name: str) -> List[str]:
        if not self.bidder_documents:
            self.parse_bidder_documents()
        if bidder_name in self.bidder_documents:
            return self.bidder_documents[bidder_name]

        # Try partial match
        for bidder, docs in self.bidder_documents.items():
            if bidder_name.lower() in bidder.lower():
                return docs
        return []

    def search_bidder(self, search_term: str) -> Dict[str, List[str]]:
        if not self.bidder_documents:
            self.parse_bidder_documents()
        results = {}
        for bidder, docs in self.bidder_documents.items():
            if search_term.lower() in bidder.lower():
                results[bidder] = docs
        return results

    def get_all_bidders(self) -> List[str]:
        if not self.bidder_documents:
            self.parse_bidder_documents()
        return list(self.bidder_documents.keys())

    def print_bidder_documents(self, bidder_name: str):
        docs = self.get_documents_for_bidder(bidder_name)
        if docs:
            print(f"\n{'='*60}")
            print(f"DOCUMENTS FOR: {bidder_name}")
            print(f"{'='*60}")
            for idx, doc in enumerate(docs, 1):
                print(f"{idx}. {doc}")
        else:
            print(f"\nNo documents found for: {bidder_name}")
            all_bidders = self.get_all_bidders()
            if all_bidders:
                print("Available bidders:")
                for bidder in all_bidders:
                    print(f"  - {bidder}")
            similar = self.search_bidder(bidder_name)
            if similar:
                print("Did you mean:")
                for bidder in similar:
                    print(f"  - {bidder}")

# === Quick usage function ===
def extract_documents_for_bidder(pdf_path: str, bidder_name: str) -> List[str]:
    extractor = BidderDocumentExtractor(pdf_path)
    return extractor.get_documents_for_bidder(bidder_name)


