"""
Debug database state to understand foreign key constraint issue.
"""
import asyncio
import sqlite3
from pathlib import Path
from memory import MemoryManager

async def debug_database_state():
    """Debug the current database state."""
    print("=== Database State Analysis ===\n")

    # Initialize memory system
    manager = MemoryManager()
    await manager.initialize()

    try:
        # Check database contents
        cursor = manager.storage.connection.cursor()

        # Check files table
        print("1. Files Table:")
        cursor.execute("SELECT id, path, hash FROM files ORDER BY created_at DESC")
        files = cursor.fetchall()
        print(f"   Total files: {len(files)}")
        for i, file_row in enumerate(files):
            print(f"   {i+1}. ID: {file_row['id'][:8]}... Path: {file_row['path']}")

        # Check chunks table
        print(f"\n2. Chunks Table:")
        cursor.execute("SELECT id, file_id, LENGTH(text) as text_len FROM chunks ORDER BY created_at DESC")
        chunks = cursor.fetchall()
        print(f"   Total chunks: {len(chunks)}")
        for i, chunk_row in enumerate(chunks):
            print(f"   {i+1}. ID: {chunk_row['id'][:8]}... File ID: {chunk_row['file_id'][:8]}... Text: {chunk_row['text_len']} chars")

        # Check for orphaned chunks (chunks without corresponding files)
        print(f"\n3. Orphaned Chunks Check:")
        cursor.execute("""
            SELECT c.id, c.file_id
            FROM chunks c
            LEFT JOIN files f ON c.file_id = f.id
            WHERE f.id IS NULL
        """)
        orphaned = cursor.fetchall()
        print(f"   Orphaned chunks: {len(orphaned)}")
        for orphan in orphaned:
            print(f"   - Chunk {orphan['id'][:8]}... references missing file {orphan['file_id'][:8]}...")

        # Check for foreign key constraint status
        print(f"\n4. Foreign Key Constraints:")
        cursor.execute("PRAGMA foreign_keys")
        fk_status = cursor.fetchone()[0]
        print(f"   Foreign keys enabled: {bool(fk_status)}")

        cursor.execute("PRAGMA foreign_key_check")
        fk_violations = cursor.fetchall()
        print(f"   Foreign key violations: {len(fk_violations)}")
        for violation in fk_violations:
            print(f"   - {violation}")

        # Clear database and test fresh
        print(f"\n5. Testing with Clean Database:")

        # Clear all data
        cursor.execute("DELETE FROM chunks")
        cursor.execute("DELETE FROM files")
        manager.storage.connection.commit()
        print("   Cleared all data")

        # Test file ingestion with clean state
        test_content = "# Test\nThis is a test document.\n## Section\nSome content."
        print("   Testing file ingestion...")

        # Create test file
        test_file = Path("./clean_test.md")
        test_file.write_text(test_content)

        try:
            file_id = await manager.ingest_file(test_file, {"test": "clean_state"})
            print(f"   ✅ Success! File ID: {file_id[:8]}...")

            # Verify data
            cursor.execute("SELECT COUNT(*) FROM files")
            file_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chunks")
            chunk_count = cursor.fetchone()[0]
            print(f"   Files in DB: {file_count}, Chunks in DB: {chunk_count}")

        except Exception as e:
            print(f"   ❌ Failed: {e}")

        finally:
            if test_file.exists():
                test_file.unlink()

    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(debug_database_state())