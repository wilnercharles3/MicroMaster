"""MicroMaster scraper: extracts chapters and sections from the source PDFs
of Automate the Boring Stuff with Python, 3rd Edition and its Workbook, and
writes a structured local SQLite database for the MicroMaster study app.

The scraped rows always include a `source_ref` field pointing back to the
origin PDF and page number, so attribution travels with every unit of content.
"""
__version__ = "0.1.0"
