"""
File system watcher for the memory system.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class FileWatcher:
    """
    Watches file system for changes and triggers callbacks.
    """

    def __init__(
        self,
        debounce_seconds: float = 1.5,
        batch_delay_seconds: float = 5.0,
        supported_extensions: Optional[List[str]] = None
    ):
        """
        Initialize file watcher.

        Args:
            debounce_seconds: Debounce delay for file change events
            batch_delay_seconds: Delay before processing batched changes
            supported_extensions: List of file extensions to watch
        """
        self.debounce_seconds = debounce_seconds
        self.batch_delay_seconds = batch_delay_seconds
        self.supported_extensions = set(supported_extensions or [
            '.md', '.txt', '.py', '.js', '.ts', '.html', '.css',
            '.json', '.yaml', '.yml', '.xml', '.rst', '.org'
        ])

        self.watch_paths: Set[Path] = set()
        self.callbacks: List[Callable[[List[Path]], None]] = []
        self.pending_changes: Dict[Path, datetime] = {}
        self.observer = None
        self.processing_task: Optional[asyncio.Task] = None
        self.is_watching = False

    async def start_watching(self, paths: List[Path], callback: Callable[[List[Path]], None]) -> None:
        """
        Start watching paths for changes.

        Args:
            paths: List of paths to watch
            callback: Function to call when changes are detected
        """
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            logger.warning("watchdog not available, file watching disabled")
            return

        if self.is_watching:
            await self.stop_watching()

        self.watch_paths = set(Path(p) for p in paths)
        self.callbacks = [callback]

        # Create event handler
        event_handler = self._create_event_handler()

        # Start observer
        self.observer = Observer()

        for path in self.watch_paths:
            if path.exists():
                self.observer.schedule(event_handler, str(path), recursive=True)
                logger.info(f"Watching path: {path}")

        self.observer.start()
        self.is_watching = True

        # Start background processing task
        self.processing_task = asyncio.create_task(self._process_changes_loop())

        logger.info(f"File watcher started for {len(self.watch_paths)} paths")

    async def stop_watching(self) -> None:
        """Stop watching for file changes."""
        self.is_watching = False

        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None

        self.pending_changes.clear()
        logger.info("File watcher stopped")

    def _create_event_handler(self):
        """Create watchdog event handler."""
        try:
            from watchdog.events import FileSystemEventHandler
        except ImportError:
            return None

        class ChangeHandler(FileSystemEventHandler):
            def __init__(self, watcher):
                self.watcher = watcher

            def on_modified(self, event):
                if not event.is_directory:
                    self.watcher._on_file_change(Path(event.src_path))

            def on_created(self, event):
                if not event.is_directory:
                    self.watcher._on_file_change(Path(event.src_path))

            def on_moved(self, event):
                if not event.is_directory:
                    self.watcher._on_file_change(Path(event.dest_path))

            def on_deleted(self, event):
                if not event.is_directory:
                    self.watcher._on_file_change(Path(event.src_path))

        return ChangeHandler(self)

    def _on_file_change(self, file_path: Path) -> None:
        """Handle file change event."""
        # Check if file extension is supported
        if file_path.suffix.lower() not in self.supported_extensions:
            return

        # Add to pending changes with current timestamp
        self.pending_changes[file_path] = datetime.now()

        logger.debug(f"File change detected: {file_path}")

    async def _process_changes_loop(self) -> None:
        """Background loop to process debounced file changes."""
        while self.is_watching:
            try:
                await asyncio.sleep(self.debounce_seconds)

                if not self.pending_changes:
                    continue

                # Find changes that are old enough to process
                now = datetime.now()
                ready_files = []

                for file_path, change_time in list(self.pending_changes.items()):
                    if (now - change_time).total_seconds() >= self.debounce_seconds:
                        ready_files.append(file_path)
                        del self.pending_changes[file_path]

                if ready_files:
                    logger.info(f"Processing {len(ready_files)} file changes")

                    # Call callbacks
                    for callback in self.callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(ready_files)
                            else:
                                callback(ready_files)
                        except Exception as e:
                            logger.error(f"Callback failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in change processing loop: {e}")

    async def add_path(self, path: Path) -> None:
        """Add a path to watch."""
        if not self.is_watching:
            return

        path = Path(path)
        if path in self.watch_paths:
            return

        self.watch_paths.add(path)

        if self.observer and path.exists():
            event_handler = self._create_event_handler()
            self.observer.schedule(event_handler, str(path), recursive=True)
            logger.info(f"Added watch path: {path}")

    async def remove_path(self, path: Path) -> None:
        """Remove a path from watching."""
        path = Path(path)
        self.watch_paths.discard(path)

        # Remove pending changes for this path
        to_remove = [p for p in self.pending_changes if p.is_relative_to(path)]
        for p in to_remove:
            del self.pending_changes[p]

        logger.info(f"Removed watch path: {path}")

    def get_pending_changes(self) -> List[Path]:
        """Get list of files with pending changes."""
        return list(self.pending_changes.keys())

    async def force_process_pending(self) -> None:
        """Force processing of all pending changes."""
        if not self.pending_changes:
            return

        ready_files = list(self.pending_changes.keys())
        self.pending_changes.clear()

        logger.info(f"Force processing {len(ready_files)} pending changes")

        # Call callbacks
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(ready_files)
                else:
                    callback(ready_files)
            except Exception as e:
                logger.error(f"Callback failed: {e}")


class SimpleFileWatcher:
    """
    Simplified file watcher that doesn't require watchdog.
    Uses periodic polling instead of filesystem events.
    """

    def __init__(
        self,
        poll_interval_seconds: float = 30.0,
        supported_extensions: Optional[List[str]] = None
    ):
        """
        Initialize simple file watcher.

        Args:
            poll_interval_seconds: How often to check for changes
            supported_extensions: List of file extensions to watch
        """
        self.poll_interval = poll_interval_seconds
        self.supported_extensions = set(supported_extensions or [
            '.md', '.txt', '.py', '.js', '.ts', '.html', '.css',
            '.json', '.yaml', '.yml', '.xml', '.rst', '.org'
        ])

        self.watch_paths: Set[Path] = set()
        self.callbacks: List[Callable[[List[Path]], None]] = []
        self.file_states: Dict[Path, tuple[float, int]] = {}  # path -> (mtime, size)
        self.polling_task: Optional[asyncio.Task] = None
        self.is_watching = False

    async def start_watching(self, paths: List[Path], callback: Callable[[List[Path]], None]) -> None:
        """Start watching paths for changes."""
        if self.is_watching:
            await self.stop_watching()

        self.watch_paths = set(Path(p) for p in paths)
        self.callbacks = [callback]

        # Initialize file states
        await self._scan_files()

        # Start polling task
        self.polling_task = asyncio.create_task(self._polling_loop())
        self.is_watching = True

        logger.info(f"Simple file watcher started for {len(self.watch_paths)} paths")

    async def stop_watching(self) -> None:
        """Stop watching for file changes."""
        self.is_watching = False

        if self.polling_task:
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
            self.polling_task = None

        self.file_states.clear()
        logger.info("Simple file watcher stopped")

    async def _scan_files(self) -> None:
        """Scan all watch paths and record file states."""
        self.file_states.clear()

        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            if watch_path.is_file():
                if watch_path.suffix.lower() in self.supported_extensions:
                    stat = watch_path.stat()
                    self.file_states[watch_path] = (stat.st_mtime, stat.st_size)
            else:
                # Scan directory
                for file_path in watch_path.rglob('*'):
                    if (file_path.is_file() and
                        file_path.suffix.lower() in self.supported_extensions):
                        try:
                            stat = file_path.stat()
                            self.file_states[file_path] = (stat.st_mtime, stat.st_size)
                        except OSError:
                            continue

    async def _polling_loop(self) -> None:
        """Polling loop to check for file changes."""
        while self.is_watching:
            try:
                await asyncio.sleep(self.poll_interval)

                changed_files = await self._check_for_changes()

                if changed_files:
                    logger.info(f"Detected {len(changed_files)} file changes via polling")

                    # Call callbacks
                    for callback in self.callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(changed_files)
                            else:
                                callback(changed_files)
                        except Exception as e:
                            logger.error(f"Callback failed: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")

    async def _check_for_changes(self) -> List[Path]:
        """Check for file changes since last scan."""
        changed_files = []
        new_file_states = {}

        # Check existing files
        for file_path, (old_mtime, old_size) in self.file_states.items():
            try:
                if file_path.exists():
                    stat = file_path.stat()
                    new_mtime, new_size = stat.st_mtime, stat.st_size
                    new_file_states[file_path] = (new_mtime, new_size)

                    if abs(new_mtime - old_mtime) > 1 or new_size != old_size:
                        changed_files.append(file_path)
                else:
                    # File was deleted
                    changed_files.append(file_path)
            except OSError:
                # File inaccessible, consider it changed
                changed_files.append(file_path)

        # Scan for new files
        for watch_path in self.watch_paths:
            if not watch_path.exists():
                continue

            scan_paths = [watch_path] if watch_path.is_file() else watch_path.rglob('*')

            for file_path in scan_paths:
                if (file_path.is_file() and
                    file_path.suffix.lower() in self.supported_extensions and
                    file_path not in self.file_states):
                    try:
                        stat = file_path.stat()
                        new_file_states[file_path] = (stat.st_mtime, stat.st_size)
                        changed_files.append(file_path)
                    except OSError:
                        continue

        self.file_states = new_file_states
        return changed_files