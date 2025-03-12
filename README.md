 SRA Toolkit GUI

A graphical user interface for the SRA Toolkit, built with Python and Tkinter. This application simplifies the process of downloading, converting, uploading, and validating SRA files by providing an intuitive multi-tabbed interface.

## Features

- **Download Tab**: 
  - Run prefetch and srapath commands to download SRA files.
  - Support for single and batch accession downloads.
  - Integrated file browsing and folder management.
  
- **Conversion Tab**: 
  - Convert SRA files to FASTQ (and other formats) using fastq-dump.
  - Custom parameters like gzip compression and multi-threading support.
  
- **Upload/Load Tab**: 
  - Convert data (e.g., BAM to SRA) for upload or further processing.
  - Simple input and output file selection with file browser support.
  
- **Utilities Tab**: 
  - Run additional SRA Toolkit commands such as vdb-dump, rcexplain, and read-filter-redact.
  
- **Configuration Tab**: 
  - Manage toolkit configurations, including setting AWS and GCP credentials.
  - Run vdb-config for initial setup.
  
- **Validator Tab**: 
  - Validate SRA files to ensure data integrity before further processing.
  
- **Settings Tab**: 
  - Save and persist custom defaults for parameters like gzip compression and thread count.
  - Custom defaults are stored in `sra_gui_config.json`.

## Installation

### Prerequisites

- **Python 3.x**: Ensure Python is installed on your system.
- **Tkinter**: Comes pre-installed with most Python distributions.
- **SRA Toolkit**: Must be installed and available in your system's PATH.

### Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/sra-toolkit-gui.git
   cd sra-toolkit-gui
   ```

2. **Install Dependencies:**
   This project uses only Python's standard libraries. If you decide to add more features or dependencies, consider adding a `requirements.txt` file.

## Usage

Run the GUI application with the following command:

```bash
python SRA3.2compleate.py
```

Upon launch, the application window will display multiple tabs for different functionalities (Download, Conversion, Upload/Load, Utilities, Configuration, Validator, and Settings). Use the provided buttons and fields to execute SRA Toolkit commands with ease.

## Configuration & Logging

- **Configuration File**:  
  The file `sra_gui_config.json` is used to store custom default settings (e.g., gzip compression and thread count). These settings persist between sessions.

- **Logging**:  
  Application logs are saved to `sra_gui.log`. This file records key events such as command execution and errors, which can be useful for troubleshooting.

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add some feature"
   ```
4. Push the branch:
   ```bash
   git push origin feature/your-feature
   ```
5. Open a pull request describing your changes.

For significant changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

Developed by [Prasun Dhar Tripathi](https://www.linkedin.com/in/prasun-dhar-tripathi-934214180).  
For support or inquiries, please email: [tripathidhar2025@gmail.com](mailto:tripathidhar2025@gmail.com).

## Acknowledgements

- The SRA Toolkit project for providing robust tools for handling SRA files.
- The Python and Tkinter communities for their support and resources.
