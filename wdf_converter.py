"""
--------------------------------------------------------------------------------------------------------------------
Convert Renishaw WDF files to per-spectrum TXT files or single CSV files.
--------------------------------------------------------------------------------------------------------------------
positional arguments:
  import_dir_path           Directory containing WDF files
  export_dir_path           Directory to write outputs into

options:
  -h, --help                show this help message and exit
  -f, --format {txt,csv}
                            Export format: txt (default) or csv
  -v, --verbose             Enable verbose logging
  -m, --mirror              Mirror import directory structure into export directory (default: False)
  -r, --recursive           Search for .wdf files recursively (default: False)

--------------------------------------------------------------------------------------------------------------------
Requirements
--------------------------------------------------------------------------------------------------------------------
Installation:
    pip install renishawWiRE tqdm numpy pandas

--------------------------------------------------------------------------------------------------------------------
Examples
--------------------------------------------------------------------------------------------------------------------

1. Convert each WDF file in /path/to/wdf_files to a per-spectrum TXT files in /path/to/export_dir,
mirroring the directory structure, searching recursively, with verbose output:

>>> python wdf_converter.py "/path/to/wdf_files" "/path/to/export_dir" -f txt -m -r -v

2. Convert each WDF file in /path/to/wdf_files to a single CSV file in /path/to/export_dir, without mirroring, non-recursively:

>>> python wdf_converter.py "/path/to/wdf_files" "/path/to/export_dir" -f csv

--------------------------------------------------------------------------------------------------------------------
Naming conventions for file path components
--------------------------------------------------------------------------------------------------------------------
Path Component       Variable Name       	    Description
--------------------------------------------------------------------------------------------------------------------
Full Path            file_path          	    The complete path including directories and filename.
Directory            dir_path           	    The folder containing the file (corresponds to .parent).
Filename             filename	                The base name of the file with its extension (corresponds to .name).
Stem                 stem	                    The filename without the extension (corresponds to .stem).
Suffix               extension                  The file extension including the dot (corresponds to .suffix).

"""
import os
from pathlib import Path
from typing import List, Optional, Union, Tuple

import argparse
import logging
import sys

import numpy as np
import pandas as pd
from renishawWiRE import WDFReader
from tqdm import tqdm

def get_filenames(
        dir_path: str,
        patterns: Optional[Union[List[str], str]] = None,
        recursive: bool = True,
    ) -> List[str]:
    """Get filenames in a directory, optionally filtering by filetype and recursion level.

    Parameters
    ---------- 
    dir_path: str
        The directory path to search in.
    patterns: str or list of str, optional
        The file extension(s) to filter by. If None, all files are returned.
        Must include the leading dot, e.g., '.txt' or ['.txt', '.csv'].
    recursive: bool, optional
        If True (default), search all child directories. If False, only search the top directory.

    Returns
    -------
    list[str]
        A list of all found filenames as strings.

    Examples
    --------
    >>> get_filenames('/path/to/dir', patterns='.txt', recursive=False)
    ['/path/to/dir/file1.txt', '/path/to/dir/file2.txt']

    >>> get_filenames('/path/to/dir', patterns=['.txt', '.csv'], recursive=True)
    ['/path/to/dir/file1.txt', '/path/to/dir/subdir/file2.csv']
    """
    path_obj: Path = Path(dir_path)
    found_files: List[Path] = []

    if recursive:
        # Use rglob for recursive searching (like os.walk)
        patterns: str = patterns if patterns else "*"

        for pattern in (patterns if isinstance(patterns, list) else [patterns]):
            if not pattern.startswith('*'):
                pattern = f'*{pattern}'
            # Use path_obj.rglob to recursively search
            found_files.extend(path_obj.rglob(pattern))
    else:
        # Use glob or iterdir for non-recursive searching in the top level only
        # iterdir gets immediate children, we filter for files only
        found_files = (p for p in path_obj.iterdir() if p.is_file())
        
        if patterns:
            # Further filter by file extension if specified
            found_files = (
                p for p in found_files
                if p.suffix in (patterns if isinstance(patterns, list) else [patterns])
            )
            
    # Convert Path objects to string representation and sort for deterministic order
    files = [str(file) for file in found_files]
    return sorted(files)


def mirror_dir_path_tree(
        import_dir_path: str,
        export_dir_path: str
    ) -> None:
    """Create a mirrored directory tree of `import_dir` under `export_dir`.

    Only directories are created; files are not copied. The function is idempotent.
    """
    for root, dirs, _ in os.walk(import_dir_path):
        rel = os.path.relpath(root, start=import_dir_path)
        if rel == '.':
            rel = ''
        target = os.path.join(export_dir_path, rel)
        os.makedirs(target, exist_ok=True)

def extract_and_save_spectra_to_txt(
        wdf_dir_path: str,
        txt_export_dir_path: str,
    ) -> Tuple[int, Optional[str]]:
    """Read a single WDF file and save each spectrum as a separate text file.

    Parameters
    - wdf_dir_path: path to input WDF file
    - txt_export_dir_path: directory where per-spectrum files will be written

    Returns the number of spectra written (0 on error).
    """
    logger = logging.getLogger('wdf2txt')
    try:
        reader: WDFReader = WDFReader(wdf_dir_path)
    except Exception as exc:
        return 0, f"Failed to open: {type(exc).__name__}: {exc}"

    raman_shifts: np.ndarray = np.asarray(reader.xdata)
    intensities: np.ndarray = np.asarray(reader.spectra)

    try:
        # Reshape intensities to 2D array (n_spectra, points_per_spectrum)
        intensities = np.reshape(intensities, (reader.count, reader.point_per_spectrum))
    except Exception:
        if intensities.ndim == 2:
            intensities: np.ndarray = intensities
        else:
            n_points: int = intensities.size // max(1, getattr(reader, 'count', 1))
            intensities: np.ndarray = intensities.reshape((getattr(reader, 'count', 1), n_points))

    n_spectra: int = int(intensities.shape[0])

    os.makedirs(txt_export_dir_path, exist_ok=True)

    for idx in range(n_spectra):
        # Save each spectrum as a separate txt file
        txt_export_filename: str = os.path.join(txt_export_dir_path, f"{idx}.txt")
        data: np.ndarray = np.column_stack((raman_shifts, intensities[idx]))
        np.savetxt(txt_export_filename, data, fmt='%.6f', delimiter='\t')

    return n_spectra, None


def extract_and_save_spectra_to_csv(
        wdf_dir_path: str,
        csv_export_filename: str,
    ) -> Tuple[int, Optional[str]]:
    """Read a single WDF file and save all spectra into a single CSV file.

    Returns 1 on success, 0 on failure.
    """
    logger = logging.getLogger('wdf2txt')
    try:
        reader: WDFReader = WDFReader(wdf_dir_path)
    except Exception as exc:
        return 0, f"Failed to open: {type(exc).__name__}: {exc}"

    raman_shifts = np.asarray(reader.xdata)
    spectra = np.asarray(reader.spectra)

    try:
        intensities = np.reshape(spectra, (reader.count, reader.point_per_spectrum))
    except Exception:
        if spectra.ndim == 2:
            intensities = spectra
        else:
            points = spectra.size // max(1, getattr(reader, 'count', 1))
            intensities = spectra.reshape((getattr(reader, 'count', 1), points))

    try:
        df = pd.DataFrame(intensities, columns=raman_shifts)
        df.to_csv(csv_export_filename, index=False)
    except Exception as exc:
        return 0, f"Failed to write CSV: {type(exc).__name__}: {exc}"

    return 1, None

def run_conversion(
        wdf_import_dir_path: str,
        txt_export_dir_path: str,
        export_format: str = 'txt',
        mirror: bool = False,
        recursive: bool = False,
        verbose: bool = False,
    ) -> Tuple[int, List[str]]:
    """Convert all WDF files found under `wdf_import_dir` into `txt_export_dir`.

    `export_format` may be 'txt' (default) or 'csv'.
    `mirror` controls whether the import directory tree is mirrored under the export directory (default False).
    `recursive` controls whether to search for .wdf files recursively (default False).

    Returns (successful_count, failed_basenames).
    """
    logger = logging.getLogger('wdf2txt')

    if not os.path.isdir(wdf_import_dir_path):
        raise FileNotFoundError(f"Import directory does not exist: {wdf_import_dir_path}")

    try:
        os.makedirs(txt_export_dir_path, exist_ok=True)
    except OSError as exc:
        raise OSError(f"Failed to create export directory {txt_export_dir_path}: {exc}") from exc

    # Optionally mirror directory tree (directories only)
    if mirror:
        try:
            mirror_dir_path_tree(wdf_import_dir_path, txt_export_dir_path)
        except Exception as exc:
            logger.warning("Could not fully mirror directory tree: %s", exc)

    # Find WDF files (use patterns API)
    wdf_filenames: List[str] = get_filenames(wdf_import_dir_path, patterns='.wdf', recursive=recursive)
    if not wdf_filenames:
        raise FileNotFoundError(f"No WDF files found in {wdf_import_dir_path}")

    success_count = 0
    failed: dict = {}

    n_wdf_filenames: int = len(wdf_filenames)

    # Setup progress indicator
    use_tqdm = tqdm is not None
    pbar = tqdm(total=n_wdf_filenames) if use_tqdm else None

    for idx, wdf in enumerate(wdf_filenames):
        basename = os.path.basename(wdf)
        stem, _ = os.path.splitext(basename)
        # Update progress bar or simple progress line
        if pbar is not None:
            pbar.set_description(f"{basename}")
            pbar.update(1)
        else:
            print(f"Progress: {idx+1}/{n_wdf_filenames} - {basename}")
        if verbose:
            logger.info(f"Converting [{idx+1}/{n_wdf_filenames}]: {basename} as {export_format}")

        rel_dir = os.path.relpath(os.path.dirname(wdf), start=wdf_import_dir_path)
        if rel_dir == '.':
            rel_dir = ''

        if export_format.lower() == 'txt':
            if mirror:
                txt_export_subdir = os.path.join(txt_export_dir_path, rel_dir, stem)
            else:
                txt_export_subdir = os.path.join(txt_export_dir_path, stem)
            try:
                os.makedirs(txt_export_subdir, exist_ok=True)
            except OSError as exc:
                err = f"OS error creating output dir: {exc}"
                failed.setdefault(err, []).append(basename)
                if verbose:
                    logger.error("%s", err)
                continue

            written, err = extract_and_save_spectra_to_txt(wdf, txt_export_subdir)
            if written > 0:
                success_count += 1
            else:
                if err is None:
                    err = "No spectra written"
                failed.setdefault(err, []).append(basename)
                if verbose:
                    logger.error("%s", err)
        elif export_format.lower() == 'csv':
            if mirror:
                csv_filename = os.path.join(txt_export_dir_path, rel_dir, f"{stem}.csv")
            else:
                csv_filename = os.path.join(txt_export_dir_path, f"{stem}.csv")
            try:
                os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
            except OSError as exc:
                err = f"OS error creating CSV output dir: {exc}"
                failed.setdefault(err, []).append(basename)
                if verbose:
                    logger.error("%s", err)
                continue

            written, err = extract_and_save_spectra_to_csv(wdf, csv_filename)
            if written > 0:
                success_count += 1
            else:
                if err is None:
                    err = "CSV write failed"
                failed.setdefault(err, []).append(basename)
                if verbose:
                    logger.error("%s", err)
        else:
            logger.error("Unknown export format: %s", export_format)
            failed.append(basename)

    if pbar is not None:
        pbar.close()

    total_failed = sum(len(v) for v in failed.values()) if failed else 0
    print(f"Completed: {success_count} succeeded, {total_failed} failed (out of {n_wdf_filenames})")
    if verbose and failed:
        print("Failures grouped by error:")
        for err_msg, files in failed.items():
            print(f"- {err_msg} ({len(files)}):")
            for b in files:
                print(f"    - {b}")

    # Return success count and flattened list of failed basenames
    return success_count, list({b for files in failed.values() for b in files})


def main() -> None:
    parser = argparse.ArgumentParser(description='Convert WDF files to per-spectrum TXT files or single CSV files')
    # Positional arguments
    parser.add_argument('import_dir_path', help='Directory containing WDF files')
    parser.add_argument('export_dir_path', help='Directory to write outputs into')

    # Optional arguments
    parser.add_argument('-f', '--format', type=str.lower, choices=['txt', 'csv'], default='txt', help='Export format: txt (default) or csv')
    
    # Flags
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging (default: False)')
    parser.add_argument('-m', '--mirror', action='store_true', help='Mirror import directory structure into export directory (default: False)')
    parser.add_argument('-r', '--recursive', action='store_true', help='Search for .wdf files recursively (default: False)')
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')

    try:
        success_count, failed = run_conversion(
            args.import_dir_path,
            args.export_dir_path,
            export_format=args.format,
            mirror=args.mirror,
            recursive=args.recursive,
            verbose=args.verbose,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}")
        sys.exit(2)
    except OSError as exc:
        print(f"Filesystem error: {exc}")
        sys.exit(3)
    except Exception as exc:
        print(f"Unexpected error: {exc}")
        sys.exit(1)

    print(f"Successfully converted {success_count} WDF files to {args.format.upper()} files.")
    if failed:
        print(f"Failed to convert {len(failed)} files:")

        if args.verbose:
            for b in failed:
                print(f" - {b}")

if __name__ == "__main__":
    main()
