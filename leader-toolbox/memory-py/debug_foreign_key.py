"""
Debug script to investigate foreign key constraint error.
"""
import asyncio
import logging
from pathlib import Path
from memory import MemoryManager

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_foreign_key_issue():
    """Debug the foreign key constraint error."""
    logger.info("Starting foreign key debugging...")

    # Initialize memory system
    manager = MemoryManager()
    await manager.initialize()

    try:
        # Create a small test file
        test_file = Path("./test_document.md")
        test_content = """# Test Document

This is a test document for debugging foreign key issues.

## Section 1
Some content here.

## Section 2
More content here.
"""
        test_file.write_text(test_content)

        logger.info(f"Created test file: {test_file}")
        logger.info(f"File exists: {test_file.exists()}")
        logger.info(f"File size: {test_file.stat().st_size} bytes")

        # Try to process the file step by step
        logger.info("Step 1: Processing file with file processor...")
        file_info, chunks = await manager.file_processor.process_file(test_file, {"test": True})

        logger.info(f"File info created:")
        logger.info(f"  ID: {file_info.id}")
        logger.info(f"  Path: {file_info.path}")
        logger.info(f"  Hash: {file_info.hash}")
        logger.info(f"  Size: {file_info.size}")

        logger.info(f"Chunks created: {len(chunks)}")
        for i, chunk in enumerate(chunks):
            logger.info(f"  Chunk {i}:")
            logger.info(f"    ID: {chunk.id}")
            logger.info(f"    File ID: {chunk.file_id}")
            logger.info(f"    Text length: {len(chunk.text)}")

        # Step 2: Add file to storage
        logger.info("Step 2: Adding file to storage...")
        stored_file_id = await manager.storage.add_file(file_info)
        logger.info(f"Stored file ID: {stored_file_id}")
        logger.info(f"Original file ID: {file_info.id}")
        logger.info(f"IDs match: {stored_file_id == file_info.id}")

        # Verify file was added
        logger.info("Step 3: Verifying file in database...")
        retrieved_file = await manager.storage.get_file(stored_file_id)
        if retrieved_file:
            logger.info(f"File retrieved successfully: {retrieved_file.path}")
        else:
            logger.error("File not found in database!")

        # Step 4: Check what's in the files table
        logger.info("Step 4: Checking files table...")
        cursor = manager.storage.connection.cursor()
        cursor.execute("SELECT id, path FROM files")
        files = cursor.fetchall()
        logger.info(f"Files in database: {len(files)}")
        for file_row in files:
            logger.info(f"  File: {file_row['id']} -> {file_row['path']}")

        # Step 5: Try to add chunks one by one
        logger.info("Step 5: Adding chunks to storage...")
        for i, chunk in enumerate(chunks):
            try:
                logger.info(f"Adding chunk {i} (file_id: {chunk.file_id})...")

                # Generate embedding
                embedding = await manager.embeddings.embed_single(chunk.text)
                logger.info(f"  Generated embedding: {embedding.shape}")

                # Add chunk
                chunk_id = await manager.storage.add_chunk(chunk, embedding)
                logger.info(f"  Successfully added chunk: {chunk_id}")

            except Exception as e:
                logger.error(f"  Failed to add chunk {i}: {e}")
                # Let's check what's wrong
                logger.info(f"  Chunk file_id: {chunk.file_id}")
                logger.info(f"  Stored file_id: {stored_file_id}")

                # Check if file exists in database
                cursor.execute("SELECT COUNT(*) FROM files WHERE id = ?", (chunk.file_id,))
                count = cursor.fetchone()[0]
                logger.info(f"  Files with chunk.file_id: {count}")

                cursor.execute("SELECT COUNT(*) FROM files WHERE id = ?", (stored_file_id,))
                count = cursor.fetchone()[0]
                logger.info(f"  Files with stored_file_id: {count}")

                # Show the actual file IDs in database
                cursor.execute("SELECT id FROM files")
                db_ids = [row[0] for row in cursor.fetchall()]
                logger.info(f"  All file IDs in database: {db_ids}")

                raise

    finally:
        # Clean up
        await manager.close()
        if Path("./test_document.md").exists():
            Path("./test_document.md").unlink()
        logger.info("Cleanup completed")

if __name__ == "__main__":
    asyncio.run(debug_foreign_key_issue())