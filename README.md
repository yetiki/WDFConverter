# WDFConverter
A Python command-line tool for converting Renishaw WDF Raman spectroscopy files into accessible formats for data sharing. Spectra may be extracted as either:
- Individual TXT files (one file per spectrum), or
- Consolidated CSV files (one file per WDF)

The tool is designed for batch processing and can optionally preserve existing folder structure.

## Installation
### 1. Install Python

Ensure you have Python 3 installed. Check this by running:
```bash
python --version
```

If Python is not installed, download it from:
https://www.python.org/downloads/

### 2. Install Required Packages

Install the required dependencies using pip:
```bash
pip install renishawWiRE tqdm numpy pandas
```

## Usage

Run the converter from the command line:
```bash
python wdf_converter.py <import_dir_path> <export_dir_path> [options]
```

### Required Arguments
* `import_dir_path`: Path to folder containing `.wdf` files.
* `export_dir_path`: Path to folder where converted files will be saved.

### Optional Arguments
* `-f, --format {txt,csv}`: Output format.
  * `txt`:
    * Creates one `.txt` file per spectrum.
    * For each `.wdf` file, a parent folder, with the same basename as the WDF file, is created in the export directory.
    * Each spectrum contained in the `.wdf` file is then exported as a seperate individual `.txt` file inside this folder.
  * `csv`: 
    * Creates one `.csv` file per `.wdf` file.
    * For each `.wdf` file, a single `.csv` file, with the same basename as the WDF file, containing all spectra is exported.
    * The first row of the `.csv` corresponds to the raman shift values.
    * Subsequent rows of the `.csv` correspond to the intensities of each spectrum contained in the WDF file.
    
  Default: `txt`

#### Flags
* `-m, --mirror`: Recreate the source folder structure inside the export directory. (Default: off).
* `-r, --recursive`: Search for `.wdf` files in all sub-folders. (Default: off).
* `-v, --verbose`: Print detailed information during conversion. (Default: off).
* `-h, --help`: Display the help message and exit.

## Examples
### Example 1: Full Recursive Batch Conversion (TXT)
Convert all .wdf files in a directory and its sub-folders to TXT files, preserve the folder structure, and show detailed progress:
```bash
python wdf_converter.py "/path/to/wdf_files" "/path/to/export_dir" -f txt -m -r -v
```
### Example 2: Simple CSV Conversion
Convert all .wdf files in a single folder into consolidated CSV files:
```bash
python wdf_converter.py "/path/to/wdf_files" "/path/to/export_dir" -f csv
```

## Quick Start
Step-by-step walkthrough for  converting `.wdf` files to `.txt` or `.csv`.

### Step 1: Prepare Your Folders
* Create a folder containing the `.wdf` files you want to convert (for example: `My_WDF_Files`).
* Create another empty folder where the converted files will be saved (for example: `Converted_Files`).
* Note where the `wdf_converter.py` file is located on your computer (for example: inside a folder called `WDFConverter`).

### Step 2: Open a Command Window
* Windows
  1. Press `Win` + `R`
  2. Type `cmd`
  3. Press **Enter**
* macOS: Open Terminal via Applications → Utilities → Terminal
* Linux: Open your preferred terminal application.

### Step 3: Navigate to the Converter Folder
Before running the tool, you must change the terminal’s working directory to where `wdf_converter.py` is stored.
1. In the terminal, type `cd` followed by the path to the folder containing `wdf_converter.py`.
   
  **Example:**
  ```bash
  cd "path/to/WDFConverter"
  ```
2. Press **Enter**.
You are now “inside” the folder that contains the converter script.

**Tip:**
* On Windows and macOS, you can often drag the folder into the terminal after typing cd to automatically insert the path.

### Step 4: Run the Converter
Still in the command window, run the conversion command.

**Example**
```bash
python wdf_converter.py "path/to/My_WDF_Files" "path/to/Converted_Files"
```
Then press **Enter**.

The tool will:
* Find `.wdf` files in the input folder
* Convert them to `.txt` files
* Save the results in the output folder

A progress bar will appear while the files are being processed.

### Step 5: (Optional) Convert to CSV Instead
To create CSV files rather than TXT files, type `-f csv` or `--format csv` after the export directory.

**Example**
```bash
python wdf_converter.py "path/to/My_WDF_Files" "path/to/Converted_Files" -f csv
```

### Step 6: Check Your Results
Open the output folder you created. You should now see:
* TXT files (one per spectrum), or
* CSV files (one per WDF file)

These files can be opened in Excel, LibreOffice, or a standard text editor.

### Helpful Notes
* Always use quotes around folder paths, especially if they contain spaces.
* To confirm Python is installed, run:
  ```bash
  python --version
  ```
* If you see an error message, it usually means:
  * Python is not installed
  * A required package is missing
  * A folder path is incorrect

## Output Notes
* TXT output produces one file per spectrum.
* CSV output produces one file per WDF file.
* Existing files in the export directory may be overwritten.

## Requirements
* `Python 3.x`
* `renishawWiRE`
* `tqdm`
* `numpy`
* `pandas`
