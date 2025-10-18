#!/usr/bin/env python3
"""
Batch PDF Ingestion - Process PDF in small batches to avoid rate limits

This processes your PDF 5 pages at a time, so you can run it multiple times
without hitting rate limits. Run this script 4 times to process all 20 pages.

Usage:
    python ingest_batch.py

Each run: ~1 minute, ~$0.15
Total: 4 runs = ~4 minutes, ~$0.60
"""

import time
from pathlib import Path
from pdf2image import convert_from_path
from src.data_loader import _process_pdf_with_vision
from src.text_processor import chunk_text
from src.vector_store import get_vector_database_collection, embed_and_store_chunks

# Configuration
BATCH_SIZE = 5  # Pages per batch
PDF_PATH = Path("./data/RagPresenetation.pdf")
DB_PATH = "./chroma_db"

# Track progress
PROGRESS_FILE = Path("./.pdf_progress")

def get_last_processed_page():
    """Get the last successfully processed page number"""
    if PROGRESS_FILE.exists():
        return int(PROGRESS_FILE.read_text().strip())
    return 0

def save_progress(page_num):
    """Save progress"""
    PROGRESS_FILE.write_text(str(page_num))

def main():
    print("\n" + "="*70)
    print("BATCH PDF INGESTION - Processing 5 pages at a time")
    print("="*70)

    # Get progress
    last_page = get_last_processed_page()
    start_page = last_page + 1
    end_page = min(start_page + BATCH_SIZE - 1, 20)

    print(f"\n📄 Processing pages {start_page}-{end_page} of 20")
    print(f"   Progress: {last_page}/20 pages already done")
    print(f"   Estimated time: ~1 minute")
    print(f"   Estimated cost: ~${(end_page - start_page + 1) * 0.03:.2f}\n")

    if last_page >= 20:
        print("✅ All pages already processed!")
        print("\n💡 Now ingest the video:")
        print("   Run: python ingest_video.py")
        return

    # Convert only the pages we need
    print(f"📄 Converting pages {start_page}-{end_page} to images...")
    images = convert_from_path(
        str(PDF_PATH),
        first_page=start_page,
        last_page=end_page
    )
    print(f"✅ Converted {len(images)} pages")

    # Process with Vision API
    from openai import AzureOpenAI
    from src.config import settings
    from tqdm import tqdm
    import base64
    from io import BytesIO

    client = AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.openai_api_version,
    )

    all_descriptions = []
    print(f"\n⏳ Processing {len(images)} pages with Vision API (6s delay between pages)...\n")

    for i, image in enumerate(tqdm(images, desc="Vision API", unit="page")):
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        try:
            response = client.chat.completions.create(
                model=settings.llm_model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe the content of this page from a document. Include all text, titles, headings, and describe any figures, charts, tables, or diagrams."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{img_base64}"}
                        },
                    ],
                }],
                max_tokens=2048,
            )

            description = response.choices[0].message.content
            if description:
                all_descriptions.append(description)

            # Save progress after each successful page
            save_progress(start_page + i)

            # Wait 6 seconds between pages
            if i < len(images) - 1:
                time.sleep(6)

        except Exception as e:
            tqdm.write(f"⚠️  Error on page {start_page + i}: {str(e)[:100]}")
            break

    if not all_descriptions:
        print("\n❌ No pages processed successfully")
        return

    # Combine all text
    pdf_text = "\n\n".join(all_descriptions)
    print(f"\n✅ Processed {len(all_descriptions)} pages")

    # Create document
    doc = {"source": f"RagPresenetation.pdf (pages {start_page}-{end_page})", "content": pdf_text}

    # Chunk
    print("\n📝 Chunking text...")
    chunks = chunk_text([doc])
    print(f"✅ Created {len(chunks)} chunks")

    # Store
    print("\n🗄️  Storing in database...")
    collection = get_vector_database_collection(db_path=DB_PATH)
    embed_and_store_chunks(chunks, collection)

    total_chunks = collection.count()
    print(f"✅ Database now has {total_chunks} chunks total")

    # Show next steps
    pages_done = get_last_processed_page()
    pages_remaining = 20 - pages_done

    print("\n" + "="*70)
    if pages_remaining > 0:
        print(f"✅ Batch complete! {pages_done}/20 pages done")
        print(f"   {pages_remaining} pages remaining")
        print(f"\n💡 Run this script {(pages_remaining + BATCH_SIZE - 1) // BATCH_SIZE} more time(s) to finish the PDF")
    else:
        print("✅ ALL PDF PAGES COMPLETE!")
        print("\n💡 Next: Process the video")
        print("   Run: python ingest_video.py")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
