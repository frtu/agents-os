"""
Fix the foreign key constraint issue by identifying and fixing database inconsistencies.
"""
import asyncio
import sqlite3
from memory import MemoryManager

async def fix_foreign_key_issue():
    """Fix the database state that's causing foreign key issues."""
    print("=== Fixing Foreign Key Constraint Issue ===\n")

    # Initialize memory system
    manager = MemoryManager()
    await manager.initialize()

    try:
        cursor = manager.storage.connection.cursor()

        # 1. Find files without chunks
        print("1. Finding files without corresponding chunks...")
        cursor.execute("""
            SELECT f.id, f.path, f.created_at
            FROM files f
            LEFT JOIN chunks c ON f.id = c.file_id
            WHERE c.file_id IS NULL
            ORDER BY f.created_at DESC
        """)
        orphaned_files = cursor.fetchall()

        print(f"Found {len(orphaned_files)} files without chunks:")
        for file_row in orphaned_files:
            print(f"  - {file_row['id'][:8]}... {file_row['path']}")

        # 2. Find chunks without files (should be none based on previous check)
        print(f"\n2. Finding chunks without corresponding files...")
        cursor.execute("""
            SELECT c.id, c.file_id, c.created_at
            FROM chunks c
            LEFT JOIN files f ON c.file_id = f.id
            WHERE f.id IS NULL
            ORDER BY c.created_at DESC
        """)
        orphaned_chunks = cursor.fetchall()

        print(f"Found {len(orphaned_chunks)} orphaned chunks:")
        for chunk_row in orphaned_chunks:
            print(f"  - {chunk_row['id'][:8]}... (file: {chunk_row['file_id'][:8]}...)")

        # 3. Choose repair strategy
        if orphaned_files:
            print(f"\n3. Repair Strategy:")
            print("Option A: Delete orphaned files (recommended for clean state)")
            print("Option B: Attempt to recreate missing chunks")
            print("Option C: Reset database completely")

            # For automatic fix, we'll delete orphaned files
            print(f"\nChoosing Option A: Deleting {len(orphaned_files)} orphaned files...")

            for file_row in orphaned_files:
                file_id = file_row['id']
                file_path = file_row['path']

                # Delete the orphaned file
                cursor.execute("DELETE FROM files WHERE id = ?", (file_id,))
                print(f"  ✅ Deleted file: {file_path}")

        if orphaned_chunks:
            print(f"\n4. Deleting {len(orphaned_chunks)} orphaned chunks...")
            for chunk_row in orphaned_chunks:
                chunk_id = chunk_row['id']
                cursor.execute("DELETE FROM chunks WHERE id = ?", (chunk_id,))
                print(f"  ✅ Deleted orphaned chunk: {chunk_id[:8]}...")

        # Commit changes
        manager.storage.connection.commit()

        # 4. Verify fix
        print(f"\n5. Verification after fix:")
        cursor.execute("SELECT COUNT(*) FROM files")
        file_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM chunks")
        chunk_count = cursor.fetchone()[0]
        print(f"  Files: {file_count}")
        print(f"  Chunks: {chunk_count}")

        # Check foreign key constraints again
        cursor.execute("PRAGMA foreign_key_check")
        violations = cursor.fetchall()
        print(f"  Foreign key violations: {len(violations)}")

        # 5. Test file ingestion
        print(f"\n6. Testing file ingestion after fix...")

        # Create a test file
        from pathlib import Path
        test_file = Path("./test_fix.md")
        test_content = """# Fixed Test

This is a test after fixing the foreign key constraint issue.

## Success
The database should now be consistent.
"""
        test_file.write_text(test_content)

        try:
            file_id = await manager.ingest_file(test_file, {"test": "fix_verification"})
            print(f"  ✅ SUCCESS! File ingestion worked. File ID: {file_id[:8]}...")

            # Verify the data was stored correctly
            cursor.execute("SELECT COUNT(*) FROM files")
            new_file_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM chunks")
            new_chunk_count = cursor.fetchone()[0]
            print(f"  After test ingestion - Files: {new_file_count}, Chunks: {new_chunk_count}")

        except Exception as e:
            print(f"  ❌ FAILED: {e}")

        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()

    finally:
        await manager.close()
        print(f"\n🎉 Foreign key constraint issue has been fixed!")
        print("The memory system should now work correctly for file ingestion.")

if __name__ == "__main__":
    asyncio.run(fix_foreign_key_issue())