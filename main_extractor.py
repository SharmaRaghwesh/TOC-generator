import PyPDF2
import re
from collections import defaultdict
from typing import Dict, List, Optional
import pdfplumber

class BidderDocumentExtractor:
    def __init__(self, pdf_path: str):
        """
        Initialize the extractor with a PDF file path

        Args:
            pdf_path (str): Path to the PDF file containing bidder documents
        """
        self.pdf_path = pdf_path
        self.bidder_documents = defaultdict(list)
        self.raw_text = ""

    def extract_text_from_pdf(self) -> str:
        """
        Extract all text from the PDF file using both PyPDF2 and pdfplumber

        Returns:
            str: Complete text content of the PDF
        """
        try:
            # First try with pdfplumber (better for tables)
            try:
                import pdfplumber
                with pdfplumber.open(self.pdf_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"

                    if text.strip():
                        self.raw_text = text
                        return text
            except ImportError:
                print("pdfplumber not available, using PyPDF2...")

            # Fallback to PyPDF2
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

                self.raw_text = text
                return text

        except Exception as e:
            print(f"Error reading PDF: {e}")
            return ""

    def parse_bidder_documents(self) -> Dict[str, List[str]]:
        """
        Parse the PDF text to extract bidder names and their associated documents
        Handles table format with columns: S.No, File Name, Context Type, Description, Placed At

        Returns:
            Dict[str, List[str]]: Dictionary with bidder names as keys and list of documents as values
        """
        if not self.raw_text:
            self.extract_text_from_pdf()

        # Debug: print raw text to understand structure
        # print("Raw text preview:")
        # print(self.raw_text[:1000])
        # print("=" * 50)

        # Split text into lines for processing
        lines = self.raw_text.split('\n')

        current_bidder = None
        in_table_section = False

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Look for bidder names (company names in caps)
            # Pattern: COMPANY NAME-LOCATION (without asterisks in actual PDF)
            if re.match(r'^[A-Z][A-Z\s]+-[A-Z]+$', line) or \
               re.match(r'^[A-Z][A-Z\s&\.]+ LIMITED-[A-Z]+$', line) or \
               re.match(r'^[A-Z][A-Z\s&\.]+ PAINTS-[A-Z]+$', line):
                current_bidder = line
                in_table_section = False
                # print(f"Found bidder: {current_bidder}")
                continue

            # Check if we're entering the table header section
            if current_bidder and ('File Name' in line or 'S.' in line):
                # Look ahead to see if this is the table header
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if 'No.' in next_line or any(word in next_line.lower() for word in ['context', 'description', 'placed']):
                        in_table_section = True
                        print(f"Found table header for {current_bidder}")
                        continue

            # Extract document names when in table section
            if current_bidder and in_table_section:
                # Look for lines that start with numbers (table rows)
                # Pattern: number followed by filename
                if re.match(r'^\d+\s+', line):
                    # Extract the filename part
                    parts = line.split()
                    if len(parts) >= 2:
                        # The filename should be the second part (after the number)
                        filename = parts[1]
                        # Check if it's a valid filename
                        if '.' in filename and (filename.lower().endswith('.pdf') or
                                              filename.lower().endswith('.doc') or
                                              filename.lower().endswith('.docx')):
                            self.bidder_documents[current_bidder].append(filename)
                            # print(f"Added document: {filename}")
                        else:
                            # Sometimes the filename might be split across multiple parts
                            # Try to reconstruct it
                            for j in range(2, len(parts)):
                                potential_filename = ' '.join(parts[1:j+1])
                                if '.' in potential_filename and (potential_filename.lower().endswith('.pdf') or
                                                                potential_filename.lower().endswith('.doc') or
                                                                potential_filename.lower().endswith('.docx')):
                                    self.bidder_documents[current_bidder].append(potential_filename)
                                    print(f"Added reconstructed document: {potential_filename}")
                                    break
                    continue

                # Alternative: look for PDF files directly in the line
                pdf_match = re.search(r'(\S+\.pdf)', line, re.IGNORECASE)
                if pdf_match:
                    filename = pdf_match.group(1)
                    if filename not in self.bidder_documents[current_bidder]:
                        self.bidder_documents[current_bidder].append(filename)
                        print(f"Added PDF file: {filename}")
                    continue

                # If we encounter another bidder name, stop processing current table
                if re.match(r'^[A-Z][A-Z\s]+-[A-Z]+$', line):
                    in_table_section = False

        return dict(self.bidder_documents)

    def parse_bidder_documents_alternative(self) -> Dict[str, List[str]]:
        """
        Alternative parsing method using regex patterns
        """
        if not self.raw_text:
            self.extract_text_from_pdf()

        # More flexible approach - look for patterns in the text
        bidder_docs = defaultdict(list)

        # Find all PDF files in the text
        pdf_files = re.findall(r'(\S+\.pdf)', self.raw_text, re.IGNORECASE)

        # Find bidder names
        bidder_pattern = r'([A-Z][A-Z\s&\.]+ (?:PAINTS|LIMITED)-[A-Z]+)'
        bidders = re.findall(bidder_pattern, self.raw_text)

        print(f"Found {len(pdf_files)} PDF files")
        print(f"Found {len(bidders)} bidders")

        # Simple approach: associate files with the nearest bidder
        text_lines = self.raw_text.split('\n')
        current_bidder = None

        for line in text_lines:
            line = line.strip()

            # Check if line contains a bidder name
            for bidder in bidders:
                if bidder in line:
                    current_bidder = bidder
                    break

            # Check if line contains a PDF file
            if current_bidder:
                pdf_match = re.search(r'(\S+\.pdf)', line, re.IGNORECASE)
                if pdf_match:
                    filename = pdf_match.group(1)
                    bidder_docs[current_bidder].append(filename)

        return dict(bidder_docs)

    def get_documents_for_bidder(self, bidder_name: str) -> List[str]:
        """
        Get all documents for a specific bidder

        Args:
            bidder_name (str): Name of the bidder to search for

        Returns:
            List[str]: List of document names for the bidder
        """
        # Parse documents if not already done
        if not self.bidder_documents:
            self.parse_bidder_documents()

            # If still empty, try alternative method
            if not self.bidder_documents:
                print("Primary parsing failed, trying alternative method...")
                self.bidder_documents = self.parse_bidder_documents_alternative()

        # Exact match first
        if bidder_name in self.bidder_documents:
            return self.bidder_documents[bidder_name]

        # Partial match (case-insensitive)
        for bidder, documents in self.bidder_documents.items():
            if bidder_name.lower() in bidder.lower():
                return documents

        return []

    def search_bidder(self, search_term: str) -> Dict[str, List[str]]:
        """
        Search for bidders containing the search term

        Args:
            search_term (str): Term to search for in bidder names

        Returns:
            Dict[str, List[str]]: Dictionary of matching bidders and their documents
        """
        if not self.bidder_documents:
            self.parse_bidder_documents()

        results = {}
        search_term = search_term.lower()

        for bidder, documents in self.bidder_documents.items():
            if search_term in bidder.lower():
                results[bidder] = documents

        return results

    def get_all_bidders(self) -> List[str]:
        """
        Get list of all bidder names

        Returns:
            List[str]: List of all bidder names found in the PDF
        """
        if not self.bidder_documents:
            self.parse_bidder_documents()

        return list(self.bidder_documents.keys())

    def print_bidder_documents(self, bidder_name: str):
        """
        Print all documents for a specific bidder in a formatted way

        Args:
            bidder_name (str): Name of the bidder
        """
        documents = self.get_documents_for_bidder(bidder_name)

        if documents:
            print(f"\n{'='*60}")
            print(f"DOCUMENTS FOR: {bidder_name}")
            print(f"{'='*60}")
            print(f"Total Documents: {len(documents)}")
            print("-" * 40)

            for i, doc in enumerate(documents, 1):
                print(f"{i:2d}. {doc}")
        else:
            print(f"\nNo documents found for bidder: {bidder_name}")

            # Show all available bidders
            all_bidders = self.get_all_bidders()
            if all_bidders:
                print(f"\nAvailable bidders:")
                for bidder in all_bidders:
                    print(f"  - {bidder}")

            # Suggest similar bidders
            similar_bidders = self.search_bidder(bidder_name)
            if similar_bidders:
                print(f"\nDid you mean one of these bidders?")
                for bidder in similar_bidders.keys():
                    print(f"  - {bidder}")


# def main():
#     """
#     Main function to demonstrate usage
#     """
#     # Replace with your PDF file path
#     pdf_path = "/content/brief_filled_paint.pdf"

#     try:
#         # Initialize extractor
#         extractor = BidderDocumentExtractor(pdf_path)

#         # Parse the PDF
#         print("Extracting text from PDF...")
#         extractor.extract_text_from_pdf()

#         print("Parsing bidder documents...")
#         bidder_docs = extractor.parse_bidder_documents()

#         print(f"\nFound {len(bidder_docs)} bidders in the PDF:")
#         print("-" * 50)

#         for bidder in extractor.get_all_bidders():
#             doc_count = len(extractor.get_documents_for_bidder(bidder))
#             print(f"• {bidder} ({doc_count} documents)")

#         # Test specific bidder
#         bidder_name = "MOHAN PAINTS-LUCKNOW"
#         print(f"\nTesting search for: {bidder_name}")
#         extractor.print_bidder_documents(bidder_name)

#     except FileNotFoundError:
#         print(f"Error: PDF file '{pdf_path}' not found.")
#         print("Please make sure the file path is correct.")
#     except Exception as e:
#         print(f"An error occurred: {e}")


# Alternative function for direct usage
def extract_documents_for_bidder(pdf_path: str, bidder_name: str) -> List[str]:
    """
    Quick function to extract documents for a specific bidder

    Args:
        pdf_path (str): Path to the PDF file
        bidder_name (str): Name of the bidder to search for

    Returns:
        List[str]: List of document names for the bidder
    """
    extractor = BidderDocumentExtractor(pdf_path)
    return extractor.get_documents_for_bidder(bidder_name)

