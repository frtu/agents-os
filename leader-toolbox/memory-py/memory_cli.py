"""
Command-line interface for the memory system.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List
import click

from memory import MemoryManager, load_memory_config
from memory.models import SearchOptions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to memory config file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, config, verbose):
    """Memory System CLI - Manage and search your knowledge base."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize context
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config
    ctx.obj['verbose'] = verbose

def get_memory_manager(config_path: Optional[str] = None) -> MemoryManager:
    """Get initialized memory manager."""
    if config_path:
        config = load_memory_config(config_path)
    else:
        config = load_memory_config()

    return MemoryManager(config)

@cli.command()
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text')
@click.pass_context
def status(ctx, output_format):
    """Show memory system status and statistics."""

    async def _status():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()
            status_info = await manager.get_status()

            if output_format == 'json':
                click.echo(json.dumps(status_info.dict(), indent=2, default=str))
            else:
                click.echo("Memory System Status")
                click.echo("=" * 50)
                click.echo(f"Backend: {status_info.backend}")
                if status_info.storage_path:
                    click.echo(f"Storage: {status_info.storage_path}")
                click.echo(f"Health: {'✓ Healthy' if status_info.is_healthy else '✗ Issues'}")
                click.echo()

                click.echo("Statistics:")
                click.echo(f"  Files: {status_info.total_files:,}")
                click.echo(f"  Chunks: {status_info.total_chunks:,}")
                click.echo(f"  Embeddings: {status_info.total_embeddings:,}")
                click.echo(f"  Storage Size: {status_info.storage_size_mb:.1f} MB")
                click.echo(f"  Cache Size: {status_info.cache_size:,}")

                if status_info.last_sync:
                    click.echo(f"  Last Sync: {status_info.last_sync}")

                click.echo()
                click.echo("Embedding Providers:")
                for provider in status_info.embedding_providers:
                    status_icon = "✓" if provider.available else "✗"
                    click.echo(f"  {status_icon} {provider.name} ({provider.model})")
                    if provider.dimensions:
                        click.echo(f"    Dimensions: {provider.dimensions}")
                    if provider.error:
                        click.echo(f"    Error: {provider.error}")

        finally:
            await manager.close()

    asyncio.run(_status())

@cli.command()
@click.argument('query')
@click.option('--mode', type=click.Choice(['vector', 'keyword', 'hybrid']), default='hybrid')
@click.option('--max-results', '-n', type=int, default=5)
@click.option('--min-score', type=float, default=0.3)
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text')
@click.pass_context
def search(ctx, query, mode, max_results, min_score, output_format):
    """Search the memory system."""

    async def _search():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()

            options = SearchOptions(
                mode=mode,
                max_results=max_results,
                min_score=min_score
            )

            results = await manager.search(query, options)

            if output_format == 'json':
                results_data = [result.dict() for result in results]
                click.echo(json.dumps(results_data, indent=2, default=str))
            else:
                click.echo(f"Search Results for: '{query}'")
                click.echo("=" * 50)
                click.echo(f"Mode: {mode} | Results: {len(results)} | Min Score: {min_score}")
                click.echo()

                if not results:
                    click.echo("No results found.")
                    return

                for i, result in enumerate(results, 1):
                    click.echo(f"{i}. {result.file_path} (score: {result.score:.3f})")
                    click.echo(f"   Range: {result.start_char}-{result.end_char}")

                    # Show excerpt
                    excerpt = result.excerpt or result.text[:200]
                    if len(excerpt) > 200:
                        excerpt = excerpt[:200] + "..."

                    click.echo(f"   {excerpt}")
                    click.echo()

        finally:
            await manager.close()

    asyncio.run(_search())

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--metadata', type=str, help='JSON metadata for the file')
@click.pass_context
def ingest_file(ctx, file_path, metadata):
    """Ingest a file into the memory system."""

    async def _ingest():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()

            file_metadata = {}
            if metadata:
                try:
                    file_metadata = json.loads(metadata)
                except json.JSONDecodeError as e:
                    click.echo(f"Error parsing metadata JSON: {e}", err=True)
                    return

            click.echo(f"Ingesting file: {file_path}")

            file_id = await manager.ingest_file(file_path, file_metadata)

            # Get stats
            chunks = await manager.storage.get_chunks_by_file(file_id)

            click.echo(f"✓ File ingested successfully")
            click.echo(f"  File ID: {file_id}")
            click.echo(f"  Chunks created: {len(chunks)}")

        except Exception as e:
            click.echo(f"✗ Ingestion failed: {e}", err=True)
        finally:
            await manager.close()

    asyncio.run(_ingest())

@cli.command()
@click.option('--text', required=True, help='Text content to ingest')
@click.option('--title', help='Title for the text')
@click.option('--metadata', type=str, help='JSON metadata for the text')
@click.pass_context
def ingest_text(ctx, text, title, metadata):
    """Ingest text content into the memory system."""

    async def _ingest():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()

            text_metadata = {'title': title} if title else {}
            if metadata:
                try:
                    text_metadata.update(json.loads(metadata))
                except json.JSONDecodeError as e:
                    click.echo(f"Error parsing metadata JSON: {e}", err=True)
                    return

            click.echo(f"Ingesting text content ({len(text)} characters)")

            file_id = await manager.ingest_text(text, text_metadata)

            # Get stats
            chunks = await manager.storage.get_chunks_by_file(file_id)

            click.echo(f"✓ Text ingested successfully")
            click.echo(f"  File ID: {file_id}")
            click.echo(f"  Chunks created: {len(chunks)}")

        except Exception as e:
            click.echo(f"✗ Ingestion failed: {e}", err=True)
        finally:
            await manager.close()

    asyncio.run(_ingest())

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
@click.option('--pattern', multiple=True, default=['*.md', '*.txt', '*.py'], help='File patterns to include')
@click.option('--recursive/--no-recursive', default=True, help='Search subdirectories')
@click.pass_context
def ingest_directory(ctx, directory, pattern, recursive):
    """Ingest all files in a directory."""

    async def _ingest():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()

            click.echo(f"Ingesting directory: {directory}")
            click.echo(f"Patterns: {list(pattern)}")
            click.echo(f"Recursive: {recursive}")
            click.echo()

            results = await manager.file_processor.process_directory(
                directory,
                patterns=list(pattern),
                recursive=recursive,
                metadata={'source': 'directory_ingest', 'directory': str(directory)}
            )

            total_files = len(results)
            total_chunks = sum(len(chunks) for _, chunks in results)

            # Ingest all files
            click.echo("Processing files...")
            with click.progressbar(results) as bar:
                for file_info, chunks in bar:
                    # Store in memory system
                    file_id = await manager.storage.add_file(file_info)

                    for chunk in chunks:
                        embedding = await manager.embeddings.embed_single(chunk.text)
                        await manager.storage.add_chunk(chunk, embedding)

            click.echo(f"✓ Directory ingested successfully")
            click.echo(f"  Files processed: {total_files}")
            click.echo(f"  Total chunks: {total_chunks}")

        except Exception as e:
            click.echo(f"✗ Directory ingestion failed: {e}", err=True)
        finally:
            await manager.close()

    asyncio.run(_ingest())

@cli.command()
@click.option('--paths', multiple=True, help='Specific paths to sync')
@click.pass_context
def sync(ctx, paths):
    """Synchronize files with the memory system."""

    async def _sync():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()

            if paths:
                click.echo(f"Syncing {len(paths)} specific paths...")
                stats = await manager.sync_files(list(paths))
            else:
                click.echo("Syncing all configured directories...")
                stats = await manager.sync_files()

            click.echo("✓ Sync completed")
            click.echo(f"  Files processed: {stats.files_processed}")
            click.echo(f"  Files added: {stats.files_added}")
            click.echo(f"  Files updated: {stats.files_updated}")
            click.echo(f"  Processing time: {stats.processing_time_ms:.1f}ms")

            if stats.errors:
                click.echo(f"  Errors: {len(stats.errors)}")
                for error in stats.errors:
                    click.echo(f"    {error}")

        except Exception as e:
            click.echo(f"✗ Sync failed: {e}", err=True)
        finally:
            await manager.close()

    asyncio.run(_sync())

@cli.command()
@click.argument('file_id')
@click.option('--lines', help='Line range (start:end)')
@click.pass_context
def get_file(ctx, file_id, lines):
    """Get file content by ID."""

    async def _get_file():
        manager = get_memory_manager(ctx.obj.get('config_path'))

        try:
            await manager.initialize()

            # Parse line range
            line_range = None
            if lines:
                try:
                    if ':' in lines:
                        start, end = lines.split(':', 1)
                        line_range = (int(start), int(end))
                    else:
                        start = int(lines)
                        line_range = (start, start + 20)
                except ValueError:
                    click.echo("Invalid line range format", err=True)
                    return

            content = await manager.get_file(file_id, line_range)

            click.echo(f"File ID: {file_id}")
            if line_range:
                click.echo(f"Lines: {line_range[0]}-{line_range[1]}")
            click.echo("-" * 50)
            click.echo(content)

        except Exception as e:
            click.echo(f"✗ Failed to get file: {e}", err=True)
        finally:
            await manager.close()

    asyncio.run(_get_file())

@cli.group()
def config():
    """Configuration management commands."""
    pass

@config.command('show')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json']), default='text')
@click.pass_context
def show_config(ctx, output_format):
    """Show current configuration."""
    config = load_memory_config(ctx.obj.get('config_path'))

    if output_format == 'json':
        click.echo(json.dumps(config.dict(), indent=2, default=str))
    else:
        click.echo("Memory System Configuration")
        click.echo("=" * 50)
        click.echo(f"Backend: {config.backend}")
        click.echo(f"Storage Path: {config.storage_path}")
        click.echo()

        click.echo("Embeddings:")
        click.echo(f"  Provider: {config.embeddings.provider}")
        click.echo(f"  Model: {config.embeddings.model}")
        click.echo(f"  Cache Enabled: {config.embeddings.cache_embeddings}")
        click.echo()

        click.echo("Search:")
        click.echo(f"  Max Results: {config.search.max_results}")
        click.echo(f"  Min Score: {config.search.min_score}")
        click.echo(f"  Hybrid Enabled: {config.search.hybrid_enabled}")
        click.echo(f"  Vector Weight: {config.search.vector_weight}")
        click.echo()

        click.echo("Files:")
        click.echo(f"  Watch Directories: {config.files.watch_directories}")
        click.echo(f"  File Patterns: {config.files.file_patterns}")
        click.echo(f"  Auto Sync: {config.files.auto_sync}")

@config.command('validate')
@click.pass_context
def validate_config(ctx):
    """Validate configuration."""
    try:
        config = load_memory_config(ctx.obj.get('config_path'))
        click.echo("✓ Configuration is valid")

        # Test memory manager initialization
        manager = MemoryManager(config)

        async def _test():
            try:
                await manager.initialize()
                click.echo("✓ Memory system can be initialized")
                status = await manager.get_status()
                click.echo(f"✓ System health: {'Healthy' if status.is_healthy else 'Issues detected'}")
            finally:
                await manager.close()

        asyncio.run(_test())

    except Exception as e:
        click.echo(f"✗ Configuration validation failed: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    cli()