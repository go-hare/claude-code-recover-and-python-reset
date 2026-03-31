"""
File-related constants.

Port of: src/constants/files.ts
"""

BINARY_EXTENSIONS = frozenset({
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".tiff", ".tif",
    # Videos
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".wmv", ".flv", ".m4v", ".mpeg", ".mpg",
    # Audio
    ".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a", ".wma", ".aiff", ".opus",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz", ".z", ".tgz", ".iso",
    # Executables/binaries
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".obj", ".lib",
    ".app", ".msi", ".deb", ".rpm",
    # Documents
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".odt", ".ods", ".odp",
    # Fonts
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # Bytecode / VM artifacts
    ".pyc", ".pyo", ".class", ".jar", ".war", ".ear", ".node", ".wasm", ".rlib",
    # Database files
    ".sqlite", ".sqlite3", ".db", ".mdb", ".idx",
    # Design / 3D
    ".psd", ".ai", ".eps", ".sketch", ".fig", ".xd", ".blend", ".3ds", ".max",
    # Flash
    ".swf", ".fla",
    # Lock/profiling data
    ".lockb", ".dat", ".data",
})

BINARY_CHECK_SIZE = 8192


def has_binary_extension(file_path: str) -> bool:
    """Check if a file path has a binary extension."""
    dot_idx = file_path.rfind(".")
    if dot_idx == -1:
        return False
    ext = file_path[dot_idx:].lower()
    return ext in BINARY_EXTENSIONS


def is_binary_content(data: bytes) -> bool:
    """Check if data contains binary content."""
    check_size = min(len(data), BINARY_CHECK_SIZE)
    non_printable = 0
    for i in range(check_size):
        byte = data[i]
        if byte == 0:
            return True
        if byte < 32 and byte not in (9, 10, 13):
            non_printable += 1
    if check_size == 0:
        return False
    return non_printable / check_size > 0.1
