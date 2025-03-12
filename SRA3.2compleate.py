import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import threading
import time
import sys
import logging
import os
import json
import webbrowser

CONFIG_FILE = "sra_gui_config.json"

# Setup logging configuration
logging.basicConfig(
    filename='sra_gui.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info("Application started")

# --------------------------------------------------------------------
# Utility Classes and Functions
# --------------------------------------------------------------------
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
        self.tooltip = None

    def enter(self, event=None):
        try:
            x, y, _, _ = self.widget.bbox("insert")
        except Exception:
            x, y = 0, 0
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(self.tooltip, text=self.text, background="#ffffe0",
                          relief='solid', borderwidth=1)
        label.pack()

    def leave(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def load_defaults():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                defaults = json.load(f)
            logging.info("Loaded custom defaults from config file.")
            return defaults
        except Exception as e:
            logging.error("Error loading defaults: " + str(e))
    return {'gzip': False, 'threads': "1"}

def save_defaults_to_file(defaults):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(defaults, f)
        logging.info("Saved custom defaults to config file.")
    except Exception as e:
        logging.error("Error saving defaults: " + str(e))

def create_about_tab(notebook):
    about_tab = ttk.Frame(notebook)
    notebook.add(about_tab, text="About")

    # Title and Version
    title = ttk.Label(about_tab, text="SRA Toolkit GUI", font=("Arial", 14, "bold"))
    title.pack(pady=(10, 5))
    version = ttk.Label(about_tab, text="Version: F3.2", font=("Arial", 10))
    version.pack(pady=(0, 10))

    # Developer Information
    dev_info = ttk.Label(about_tab, text="Developed by: Prasun Dhar Tripathi", font=("Arial", 12, "bold"))
    dev_info.pack(pady=5)
    linkedin_link = ttk.Label(about_tab, text="LinkedIn: www.linkedin.com/in/prasun-dhar-tripathi-934214180", 
                              foreground="blue", cursor="hand2")
    linkedin_link.pack()
    linkedin_link.bind("<Button-1>", lambda e: webbrowser.open_new("https://www.linkedin.com/in/prasun-dhar-tripathi-934214180"))

    # Description
    desc = ("This GUI provides an easy-to-use front end for the SRA Toolkit. "
            "It allows you to download, convert, validate, and upload SRA files "
            "using a series of integrated commands with progress tracking, custom "
            "parameter defaults, and interactive logs.\n")
    desc_label = ttk.Label(about_tab, text=desc, wraplength=600, justify=tk.LEFT)
    desc_label.pack(padx=10, pady=10)

    # Features Section
    features_title = ttk.Label(about_tab, text="Key Features:", font=("Arial", 10, "bold"))
    features_title.pack(pady=(10, 5))
    features = (
        "- Download SRA files using prefetch and srapath",
        "- Convert SRA to FASTQ, SAM, and other formats",
        "- Upload/Load data (e.g. BAM to SRA conversion)",
        "- Validate and analyze SRA files for integrity",
        "- Customizable settings with persistent defaults",
        "- Multi-threading support for performance",
        "- Real-time progress and detailed logging"
    )
    feature_text = "\n".join(features)
    feature_box = scrolledtext.ScrolledText(about_tab, wrap=tk.WORD, width=60, height=10)
    feature_box.pack(pady=10)
    feature_box.insert(tk.END, feature_text)
    feature_box.config(state=tk.DISABLED)

    # Contact / Support
    support = ttk.Label(about_tab, text="For support or suggestions, please contact: tripathidhar2025@gmail.com", font=("Arial", 9))
    support.pack(pady=(10, 5))

    return about_tab

# --------------------------------------------------------------------
# Main Application Class
# --------------------------------------------------------------------
class SraToolkitGUI:
    def __init__(self, root):
        self.root = root
        self.current_process = None  # For subprocess handling
        self.saved_paths = {}        # To store output file/directory paths
        self.custom_defaults = load_defaults()    # load saved defaults
        self.setup_ui()

    def setup_ui(self):
        self.root.title("SRA Toolkit GUI")
        self.root.minsize(800, 600)

        # Top frame with Cancel Process button
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        self.cancel_button = ttk.Button(top_frame, text="Cancel Process", command=self.cancel_command)
        self.cancel_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Global progress bar (indeterminate)
        self.global_progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.global_progress.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)
        self.global_progress.stop()

        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.create_download_tab()
        self.create_conversion_tab()
        self.create_upload_tab()
        self.create_utilities_tab()
        self.create_configuration_tab()
        self.create_validator_tab()
        self.create_settings_tab()

        # Add About tab
        create_about_tab(self.notebook)

        # Status bar at the bottom
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<F1>', lambda e: self.show_help())

    def exit_application(self):
        self.root.quit()

    # -------------------------- Common Methods --------------------------
    def run_command(self, cmd, output_widget, progress_widget=None):
        output_widget.config(state=tk.NORMAL)
        output_widget.delete("1.0", tk.END)
        if progress_widget:
            progress_widget.config(state=tk.NORMAL)
            progress_widget.delete("1.0", tk.END)
            progress_widget.insert(tk.END, f"Starting command: {' '.join(cmd)}\n")
        command_str = ' '.join(cmd)
        self.status_bar.config(text=f"Running: {command_str}")
        output_widget.insert(tk.END, f"Running command: {command_str}\n\n")
        output_widget.update_idletasks()
        # Setup error tag for red text
        output_widget.tag_configure("error", foreground="red")

        self.global_progress.start(10)

        def execute():
            try:
                logging.info(f"Executing command: {command_str}")
                self.current_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                start_time = time.time()
                timeout = 300  # 5 minutes
                while True:
                    if time.time() - start_time > timeout:
                        self.current_process.kill()
                        output_widget.insert(tk.END, "Error: Command timed out after 5 minutes\n", "error")
                        self.status_bar.config(text="Error: Command timed out")
                        logging.error("Command timed out")
                        if progress_widget:
                            progress_widget.insert(tk.END, "Command timed out.\n")
                        break
                    stdout_line = self.current_process.stdout.readline()
                    stderr_line = self.current_process.stderr.readline()
                    if stdout_line:
                        output_widget.insert(tk.END, stdout_line)
                        output_widget.see(tk.END)
                        if progress_widget:
                            progress_widget.insert(tk.END, f"[OUTPUT] {stdout_line}")
                            progress_widget.see(tk.END)
                    if stderr_line:
                        output_widget.insert(tk.END, stderr_line, "error")
                        if progress_widget:
                            progress_widget.insert(tk.END, f"[ERROR] {stderr_line}\n")
                    if not stdout_line and not stderr_line and self.current_process.poll() is not None:
                        remaining_stdout = self.current_process.stdout.read()
                        if remaining_stdout:
                            output_widget.insert(tk.END, remaining_stdout)
                            if progress_widget:
                                progress_widget.insert(tk.END, f"[OUTPUT] {remaining_stdout}")
                        remaining_stderr = self.current_process.stderr.read()
                        if remaining_stderr:
                            output_widget.insert(tk.END, "Errors:\n" + remaining_stderr, "error")
                            if progress_widget:
                                progress_widget.insert(tk.END, f"[ERROR] {remaining_stderr}\n")
                        self.status_bar.config(text="Command completed successfully")
                        logging.info("Command completed successfully")
                        if progress_widget:
                            progress_widget.insert(tk.END, "Command completed successfully.\n")
                        break
                    time.sleep(0.1)
            except Exception as e:
                output_widget.insert(tk.END, f"Error: {str(e)}\n", "error")
                self.status_bar.config(text="Error: Execution failed")
                logging.exception("Error during command execution")
                if progress_widget:
                    progress_widget.insert(tk.END, f"[EXCEPTION] {str(e)}\n")
            finally:
                self.global_progress.stop()
                self.current_process = None
                output_widget.see("1.0")
        threading.Thread(target=execute, daemon=True).start()

    def cancel_command(self):
        if self.current_process:
            try:
                self.current_process.kill()
                self.status_bar.config(text="Process canceled")
                logging.info("Process canceled by user")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to cancel process: {str(e)}")
                logging.exception("Error cancelling process")
            finally:
                self.current_process = None
                self.global_progress.stop()
        else:
            messagebox.showinfo("Info", "No process is currently running.")

    @staticmethod
    def validate_input(entry, error_message):
        value = entry.get().strip()
        if not value:
            messagebox.showerror("Input Error", error_message)
            return None
        return value

    def create_file_browser(self, entry_widget, file_type="file"):
        def browse():
            if file_type == "file":
                filename = filedialog.askopenfilename()
            elif file_type == "dir":
                filename = filedialog.askdirectory()
            else:
                filename = ""
            if filename:
                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, filename)
        btn = ttk.Button(entry_widget.master, text="Browse", command=browse)
        ToolTip(btn, "Click to browse for a " + ("file" if file_type == "file" else "directory"))
        return btn

    def create_output_browser(self, entry_widget, key, file_type="file"):
        if file_type == "file":
            filename = filedialog.asksaveasfilename()
        elif file_type == "dir":
            filename = filedialog.askdirectory()
        else:
            filename = ""
        if filename:
            self.saved_paths[key] = filename
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, filename)

    def show_help(self):
        help_text = (
            "SRA Toolkit GUI Help\n\n"
            "Keyboard Shortcuts:\n"
            "  Ctrl+Q: Quit application\n"
            "  F1: Show this help\n"
            "  Cancel Process: Cancel the running command\n\n"
            "Tips:\n"
            "  - Use the Browse buttons to select input and output files/directories.\n"
            "  - Each tab has an 'i' button for detailed feature information.\n"
            "  - Custom parameter controls allow you to set additional options.\n"
            "  - The Progress window shows step-by-step updates while the Output window shows logs.\n"
            "  - The global progress bar indicates when a command is running."
        )
        messagebox.showinfo("Help", help_text)

    def show_tab_info(self, title, info_text):
        messagebox.showinfo(f"{title} Info", info_text)

    # -------------------------- Tab Creation Methods --------------------------
    def create_download_tab(self):
        self.download_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.download_tab, text="Download")
        info_text = (
            "Downloads SRA data files using prefetch and srapath commands.\n\n"
            "Enter a single accession below or use the batch field to download multiple files (one accession per line).\n"
            "Use this tab when you need to retrieve SRA files for further processing."
        )
        info_frame = ttk.Frame(self.download_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(info_frame, text="i", width=2,
                                 command=lambda: self.show_tab_info("Download Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        # Single accession controls
        ttk.Label(self.download_tab, text="Prefetch Accession:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.prefetch_entry = ttk.Entry(self.download_tab, width=40)
        self.prefetch_entry.grid(row=1, column=1, padx=5, pady=5)
        prefetch_button = ttk.Button(self.download_tab, text="Run Prefetch", command=self.run_prefetch)
        prefetch_button.grid(row=1, column=2, padx=5, pady=5)
        ttk.Label(self.download_tab, text="Srapath Accession:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.srapath_entry = ttk.Entry(self.download_tab, width=40)
        self.srapath_entry.grid(row=2, column=1, padx=5, pady=5)
        srapath_button = ttk.Button(self.download_tab, text="Run Srapath", command=self.run_srapath)
        srapath_button.grid(row=2, column=2, padx=5, pady=5)
        # Downloads Folder controls
        ttk.Label(self.download_tab, text="Downloads Folder:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.download_folder_entry = ttk.Entry(self.download_tab, width=40)
        self.download_folder_entry.grid(row=3, column=1, padx=5, pady=5)
        browse_folder_btn = ttk.Button(self.download_tab, text="Browse Folder", command=self.browse_download_folder)
        browse_folder_btn.grid(row=3, column=2, padx=5, pady=5)
        open_folder_btn = ttk.Button(self.download_tab, text="Open Folder", command=self.open_download_folder)
        open_folder_btn.grid(row=3, column=3, padx=5, pady=5)
        # Batch download controls
        ttk.Label(self.download_tab, text="Batch Prefetch Accessions (one per line):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.batch_prefetch_text = scrolledtext.ScrolledText(self.download_tab, wrap=tk.WORD, width=80, height=4)
        self.batch_prefetch_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        batch_button = ttk.Button(self.download_tab, text="Run Batch Prefetch", 
                                  command=lambda: threading.Thread(target=self.run_batch_prefetch, daemon=True).start())
        batch_button.grid(row=5, column=3, padx=5, pady=5)
        # Progress window
        ttk.Label(self.download_tab, text="Progress:").grid(row=6, column=0, padx=5, pady=(15, 5), sticky=tk.W)
        self.download_progress = scrolledtext.ScrolledText(self.download_tab, wrap=tk.WORD, width=80, height=6)
        self.download_progress.grid(row=7, column=0, columnspan=4, padx=5, pady=5)
        # Output window
        ttk.Label(self.download_tab, text="Output:").grid(row=8, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.download_output = scrolledtext.ScrolledText(self.download_tab, wrap=tk.WORD, width=80, height=10)
        self.download_output.grid(row=9, column=0, columnspan=4, padx=5, pady=5)

    def browse_download_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.download_folder_entry.delete(0, tk.END)
            self.download_folder_entry.insert(0, folder)

    def open_download_folder(self):
        folder = self.download_folder_entry.get().strip()
        if folder and os.path.isdir(folder):
            try:
                if os.name == 'nt':
                    os.startfile(folder)
                elif sys.platform == 'darwin':
                    subprocess.Popen(["open", folder])
                else:
                    subprocess.Popen(["xdg-open", folder])
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open folder: {str(e)}")
        else:
            messagebox.showerror("Error", "Please enter a valid downloads folder.")

    def run_prefetch(self):
        accession = self.validate_input(self.prefetch_entry, "Please enter an accession for prefetch.")
        if not accession:
            return
        self.status_bar.config(text="Running prefetch...")
        cmd = ["prefetch", "--progress", accession]
        self.run_command(cmd, self.download_output, self.download_progress)

    def run_srapath(self):
        accession = self.validate_input(self.srapath_entry, "Please enter an accession for srapath.")
        if not accession:
            return
        self.status_bar.config(text="Running srapath...")
        cmd = ["srapath", accession]
        self.run_command(cmd, self.download_output, self.download_progress)

    def run_batch_prefetch(self):
        accessions_text = self.batch_prefetch_text.get("1.0", tk.END).strip()
        if not accessions_text:
            messagebox.showerror("Input Error", "Please enter at least one accession number for batch prefetch.")
            return
        accessions = [line.strip() for line in accessions_text.splitlines() if line.strip()]
        self.status_bar.config(text="Running batch prefetch...")
        self.global_progress.start(10)
        for acc in accessions:
            self.download_output.insert(tk.END, f"\nRunning prefetch for {acc}\n")
            cmd = ["prefetch", "--progress", acc]
            try:
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.download_output.insert(tk.END, result.stdout)
                if result.stderr:
                    self.download_output.insert(tk.END, "Errors:\n" + result.stderr, "error")
            except Exception as e:
                self.download_output.insert(tk.END, f"Error running prefetch for {acc}: {str(e)}\n", "error")
            self.download_output.see(tk.END)
        self.global_progress.stop()
        self.status_bar.config(text="Batch prefetch completed")

    def create_conversion_tab(self):
        self.conversion_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.conversion_tab, text="Conversion")
        info_text = (
            "Converts SRA files to formats like FASTQ and SAM.\n\n"
            "Select the SRA file, adjust custom parameters if needed, and click the conversion button."
        )
        info_frame = ttk.Frame(self.conversion_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(info_frame, text="i", width=2,
                                 command=lambda: self.show_tab_info("Conversion Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w")
        ttk.Label(self.conversion_tab, text="Fastq-dump SRA File:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.fastqdump_entry = ttk.Entry(self.conversion_tab, width=40)
        self.fastqdump_entry.grid(row=1, column=1, padx=5, pady=5)
        fastqdump_button = ttk.Button(self.conversion_tab, text="Run Fastq-dump", command=self.run_fastq_dump)
        fastqdump_button.grid(row=1, column=2, padx=5, pady=5)
        self.create_file_browser(self.fastqdump_entry).grid(row=1, column=3, padx=5, pady=5)
        # Custom Parameter Controls
        custom_frame = ttk.LabelFrame(self.conversion_tab, text="Custom Parameters")
        custom_frame.grid(row=2, column=0, columnspan=4, padx=5, pady=10, sticky="ew")
        self.gzip_var = tk.BooleanVar(value=self.custom_defaults.get('gzip', False))
        self.gzip_check = ttk.Checkbutton(custom_frame, text="Enable gzip compression", variable=self.gzip_var)
        self.gzip_check.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(custom_frame, text="Thread Count:").grid(row=0, column=1, padx=5, pady=5, sticky="e")
        self.thread_count = ttk.Combobox(custom_frame, values=["1", "2", "4", "8"], width=5)
        self.thread_count.set(self.custom_defaults.get('threads', "1"))
        self.thread_count.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        # Progress window
        ttk.Label(self.conversion_tab, text="Progress:").grid(row=3, column=0, padx=5, pady=(15, 5), sticky=tk.W)
        self.conv_progress = scrolledtext.ScrolledText(self.conversion_tab, wrap=tk.WORD, width=80, height=6)
        self.conv_progress.grid(row=4, column=0, columnspan=4, padx=5, pady=5)
        # Output window
        ttk.Label(self.conversion_tab, text="Output:").grid(row=5, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.conv_output = scrolledtext.ScrolledText(self.conversion_tab, wrap=tk.WORD, width=80, height=10)
        self.conv_output.grid(row=6, column=0, columnspan=4, padx=5, pady=5)

    def run_fastq_dump(self):
        sra_file = self.validate_input(self.fastqdump_entry, "Please enter the SRA file path for fastq-dump.")
        if not sra_file:
            return
        self.status_bar.config(text="Running fastq-dump...")
        custom_params = []
        if self.gzip_var.get():
            custom_params.append("--gzip")
        thread = self.thread_count.get().strip()
        if thread:
            custom_params.extend(["--threads", thread])
        cmd = ["fastq-dump", "--progress"] + custom_params + [sra_file]
        self.run_command(cmd, self.conv_output, self.conv_progress)

    def create_upload_tab(self):
        self.upload_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.upload_tab, text="Upload/Load")
        info_text = (
            "Converts data (e.g. BAM to SRA) for upload or storage.\n\n"
            "Enter the BAM file path and desired output filename, then click Run."
        )
        info_frame = ttk.Frame(self.upload_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(info_frame, text="i", width=2,
                                 command=lambda: self.show_tab_info("Upload/Load Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w")
        ttk.Label(self.upload_tab, text="BAM File Path:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.bamload_bam_entry = ttk.Entry(self.upload_tab, width=40)
        self.bamload_bam_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        input_browse_btn = ttk.Button(self.upload_tab, text="Browse", 
                                      command=lambda: self.create_file_browser(self.bamload_bam_entry, file_type="file").invoke())
        input_browse_btn.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.upload_tab, text="Output SRA Filename:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.bamload_out_entry = ttk.Entry(self.upload_tab, width=40)
        self.bamload_out_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        output_browse_btn = ttk.Button(self.upload_tab, text="Browse", 
                                       command=lambda: self.create_output_browser(self.bamload_out_entry, 'bamload', file_type='file'))
        output_browse_btn.grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        bamload_button = ttk.Button(self.upload_tab, text="Run bam-load", command=self.run_bam_load)
        bamload_button.grid(row=3, column=2, padx=5, pady=15, sticky=tk.E)
        ttk.Label(self.upload_tab, text="Progress:").grid(row=4, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.upload_progress = scrolledtext.ScrolledText(self.upload_tab, wrap=tk.WORD, width=80, height=6)
        self.upload_progress.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)
        ttk.Label(self.upload_tab, text="Output:").grid(row=6, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.upload_output = scrolledtext.ScrolledText(self.upload_tab, wrap=tk.WORD, width=80, height=10)
        self.upload_output.grid(row=7, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W)

    def run_bam_load(self):
        bam_file = self.validate_input(self.bamload_bam_entry, "Please enter the BAM file path.")
        if not bam_file:
            return
        output_sra = self.validate_input(self.bamload_out_entry, "Please enter the output SRA filename.")
        if not output_sra:
            return
        self.status_bar.config(text="Running bam-load...")
        cmd = ["bam-load", "-o", output_sra, bam_file]
        self.run_command(cmd, self.upload_output, self.upload_progress)

    def create_utilities_tab(self):
        self.utilities_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.utilities_tab, text="Utilities")
        info_text = (
            "Provides commands to dump, explain, or filter SRA files.\n\n"
            "Enter the SRA file path and click the corresponding run button."
        )
        info_frame = ttk.Frame(self.utilities_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(info_frame, text="i", width=2,
                                 command=lambda: self.show_tab_info("Utilities Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w")
        ttk.Label(self.utilities_tab, text="vdb-dump SRA File:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.vdbdump_entry = ttk.Entry(self.utilities_tab, width=40)
        self.vdbdump_entry.grid(row=1, column=1, padx=5, pady=5)
        vdbdump_button = ttk.Button(self.utilities_tab, text="Run vdb-dump", command=self.run_vdb_dump)
        vdbdump_button.grid(row=1, column=2, padx=5, pady=5)
        ttk.Label(self.utilities_tab, text="rcexplain SRA File:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.rcexplain_entry = ttk.Entry(self.utilities_tab, width=40)
        self.rcexplain_entry.grid(row=2, column=1, padx=5, pady=5)
        rcexplain_button = ttk.Button(self.utilities_tab, text="Run rcexplain", command=self.run_rcexplain)
        rcexplain_button.grid(row=2, column=2, padx=5, pady=5)
        ttk.Label(self.utilities_tab, text="read-filter-redact SRA File:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.readfilter_entry = ttk.Entry(self.utilities_tab, width=40)
        self.readfilter_entry.grid(row=3, column=1, padx=5, pady=5)
        readfilter_button = ttk.Button(self.utilities_tab, text="Run read-filter-redact", command=self.run_read_filter_redact)
        readfilter_button.grid(row=3, column=2, padx=5, pady=5)
        ttk.Label(self.utilities_tab, text="Progress:").grid(row=4, column=0, padx=5, pady=(15, 5), sticky=tk.W)
        self.util_progress = scrolledtext.ScrolledText(self.utilities_tab, wrap=tk.WORD, width=80, height=6)
        self.util_progress.grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        ttk.Label(self.utilities_tab, text="Output:").grid(row=6, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.util_output = scrolledtext.ScrolledText(self.utilities_tab, wrap=tk.WORD, width=80, height=10)
        self.util_output.grid(row=7, column=0, columnspan=3, padx=5, pady=5)

    def run_vdb_dump(self):
        sra_file = self.validate_input(self.vdbdump_entry, "Please enter the SRA file path for vdb-dump.")
        if not sra_file:
            return
        self.status_bar.config(text="Running vdb-dump...")
        cmd = ["vdb-dump", sra_file]
        self.run_command(cmd, self.util_output, self.util_progress)

    def run_rcexplain(self):
        sra_file = self.validate_input(self.rcexplain_entry, "Please enter the SRA file path for rcexplain.")
        if not sra_file:
            return
        self.status_bar.config(text="Running rcexplain...")
        cmd = ["rcexplain", sra_file]
        self.run_command(cmd, self.util_output, self.util_progress)

    def run_read_filter_redact(self):
        sra_file = self.validate_input(self.readfilter_entry, "Please enter the SRA file path for read-filter-redact.")
        if not sra_file:
            return
        self.status_bar.config(text="Running read-filter-redact...")
        cmd = ["read-filter-redact", sra_file]
        self.run_command(cmd, self.util_output, self.util_progress)

    def create_configuration_tab(self):
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Configuration")
        info_text = (
            "Manages toolkit configuration, including setting AWS and GCP credentials.\n\n"
            "Enter the credentials file path and click the run button.\n\n"
            "When to Use It:\n"
            "  Use this during initial setup or when credentials change.\n\n"
            "Where to Use It:\n"
            "  Essential for configuring the SRA Toolkit environment."
        )
        info_frame = ttk.Frame(self.config_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(self.config_tab, text="i", width=2,
                                 command=lambda: self.show_tab_info("Configuration Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        vdbconfig_button = ttk.Button(self.config_tab, text="Run vdb-config", command=self.run_vdb_config)
        vdbconfig_button.grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(self.config_tab, text="AWS Credentials File:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.aws_cred_entry = ttk.Entry(self.config_tab, width=40)
        self.aws_cred_entry.grid(row=2, column=1, padx=5, pady=5)
        aws_cred_button = ttk.Button(self.config_tab, text="Set AWS Credentials", command=self.set_aws_credentials)
        aws_cred_button.grid(row=2, column=2, padx=5, pady=5)
        ttk.Label(self.config_tab, text="GCP Credentials File:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.gcp_cred_entry = ttk.Entry(self.config_tab, width=40)
        self.gcp_cred_entry.grid(row=3, column=1, padx=5, pady=5)
        gcp_cred_button = ttk.Button(self.config_tab, text="Set GCP Credentials", command=self.set_gcp_credentials)
        gcp_cred_button.grid(row=3, column=2, padx=5, pady=5)
        ttk.Label(self.config_tab, text="Progress:").grid(row=4, column=0, padx=5, pady=(15, 5), sticky=tk.W)
        self.config_progress = scrolledtext.ScrolledText(self.config_tab, wrap=tk.WORD, width=80, height=6)
        self.config_progress.grid(row=5, column=0, columnspan=3, padx=5, pady=5)
        ttk.Label(self.config_tab, text="Output:").grid(row=6, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.config_output = scrolledtext.ScrolledText(self.config_tab, wrap=tk.WORD, width=80, height=10)
        self.config_output.grid(row=7, column=0, columnspan=3, padx=5, pady=5)

    def run_vdb_config(self):
        self.status_bar.config(text="Running vdb-config...")
        cmd = ["vdb-config", "-i"]
        self.run_command(cmd, self.config_output, self.config_progress)

    def set_aws_credentials(self):
        cred_file = self.validate_input(self.aws_cred_entry, "Please enter the path to your AWS credentials file.")
        if not cred_file:
            return
        self.status_bar.config(text="Setting AWS credentials...")
        cmd = ["vdb-config", "--set-aws-credentials", cred_file]
        self.run_command(cmd, self.config_output, self.config_progress)

    def set_gcp_credentials(self):
        cred_file = self.validate_input(self.gcp_cred_entry, "Please enter the path to your GCP credentials file.")
        if not cred_file:
            return
        self.status_bar.config(text="Setting GCP credentials...")
        cmd = ["vdb-config", "--set-gcp-credentials", cred_file]
        self.run_command(cmd, self.config_output, self.config_progress)

    def create_validator_tab(self):
        self.validator_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.validator_tab, text="Validator")
        info_text = (
            "Validates SRA files to ensure data integrity.\n\n"
            "Select the SRA file and click the run button to validate.\n\n"
            "When to Use It:\n"
            "  Use this before further processing to verify file integrity.\n\n"
            "Where to Use It:\n"
            "  For quality assurance and error checking."
        )
        info_frame = ttk.Frame(self.validator_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(info_frame, text="i", width=2,
                                 command=lambda: self.show_tab_info("Validator Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w")
        ttk.Label(self.validator_tab, text="SRA Validator File:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.validator_entry = ttk.Entry(self.validator_tab, width=40)
        self.validator_entry.grid(row=1, column=1, padx=5, pady=5)
        validator_button = ttk.Button(self.validator_tab, text="Run SRA Validator", command=self.run_sra_validator)
        validator_button.grid(row=1, column=2, padx=5, pady=5)
        self.create_file_browser(self.validator_entry).grid(row=1, column=3, padx=5, pady=5)
        ttk.Label(self.validator_tab, text="Progress:").grid(row=2, column=0, padx=5, pady=(15, 5), sticky=tk.W)
        self.validator_progress = scrolledtext.ScrolledText(self.validator_tab, wrap=tk.WORD, width=80, height=6)
        self.validator_progress.grid(row=3, column=0, columnspan=4, padx=5, pady=5)
        ttk.Label(self.validator_tab, text="Output:").grid(row=4, column=0, padx=5, pady=(10, 5), sticky=tk.W)
        self.validator_output = scrolledtext.ScrolledText(self.validator_tab, wrap=tk.WORD, width=80, height=10)
        self.validator_output.grid(row=5, column=0, columnspan=4, padx=5, pady=5)

    def run_sra_validator(self):
        sra_file = self.validate_input(self.validator_entry, "Please enter the SRA file path for validation.")
        if not sra_file:
            return
        self.status_bar.config(text="Running sra-validator...")
        cmd = ["sra-validator", sra_file]
        self.run_command(cmd, self.validator_output, self.validator_progress)

    def create_settings_tab(self):
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")
        info_text = (
            "Allows you to set default custom parameters that will be applied automatically\n"
            "to SRA operations (e.g., default thread count, gzip option).\n\n"
            "Adjust the settings below and click 'Save Defaults'. These settings will pre-populate\n"
            "the custom parameter fields in the respective tabs and be saved between sessions."
        )
        info_frame = ttk.Frame(self.settings_tab)
        info_frame.grid(row=0, column=0, columnspan=4, sticky="w", padx=5, pady=5)
        info_button = ttk.Button(info_frame, text="i", width=2,
                                 command=lambda: self.show_tab_info("Settings Tab", info_text))
        info_button.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        # Default gzip option
        self.default_gzip_var = tk.BooleanVar(value=False)
        gzip_check = ttk.Checkbutton(self.settings_tab, text="Default: Enable gzip compression", variable=self.default_gzip_var)
        gzip_check.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        # Default thread count
        ttk.Label(self.settings_tab, text="Default Thread Count:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.default_thread = ttk.Combobox(self.settings_tab, values=["1", "2", "4", "8"], width=5)
        self.default_thread.set("1")
        self.default_thread.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        # Save Defaults button
        save_btn = ttk.Button(self.settings_tab, text="Save Defaults", command=self.save_defaults)
        save_btn.grid(row=3, column=0, padx=5, pady=10, sticky="w")
        # Display current defaults
        self.defaults_display = ttk.Label(self.settings_tab, text="Current Defaults: Default gzip: False, Thread Count: 1")
        self.defaults_display.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="w")

    def save_defaults(self):
        self.custom_defaults['gzip'] = self.default_gzip_var.get()
        self.custom_defaults['threads'] = self.default_thread.get()
        display_text = f"Default gzip: {self.custom_defaults['gzip']}, Thread Count: {self.custom_defaults['threads']}"
        self.defaults_display.config(text=f"Current Defaults: {display_text}")
        # Update Conversion tab controls
        self.gzip_var.set(self.custom_defaults['gzip'])
        self.thread_count.set(self.custom_defaults['threads'])
        save_defaults_to_file(self.custom_defaults)
        messagebox.showinfo("Defaults Saved", "Custom parameter defaults have been saved.")

    # -------------------------- Additional Command Methods --------------------------
    def run_rcexplain(self):
        sra_file = self.validate_input(self.rcexplain_entry, "Please enter the SRA file path for rcexplain.")
        if not sra_file:
            return
        self.status_bar.config(text="Running rcexplain...")
        cmd = ["rcexplain", sra_file]
        self.run_command(cmd, self.util_output, self.util_progress)

    def run_vdb_copy(self):
        src = self.validate_input(self.vdbcopy_src_entry, "Please enter the source VDB file for Vdb-copy.")
        dest = self.validate_input(self.vdbcopy_dest_entry, "Please enter the destination for Vdb-copy.")
        if not src or not dest:
            return
        self.status_bar.config(text="Running Vdb-copy...")
        cmd = ["vdb-copy", src, dest]
        self.run_command(cmd, self.vdbcopy_output)

    def run_abi_dump(self):
        sra_file = self.validate_input(self.abidump_entry, "Please enter the SRA file path for Abi-dump.")
        if not sra_file:
            return
        self.status_bar.config(text="Running Abi-dump...")
        cmd = ["abi-dump", sra_file]
        self.run_command(cmd, self.abidump_output)

    def run_sra_sort(self):
        sra_file = self.validate_input(self.srasort_entry, "Please enter the SRA file path for Sra-sort.")
        if not sra_file:
            return
        self.status_bar.config(text="Running Sra-sort...")
        cmd = ["sra-sort", sra_file]
        self.run_command(cmd, self.srasort_output)

    def run_kar(self):
        kar_dir = self.validate_input(self.kar_dir_entry, "Please enter the directory to package for Kar.")
        if not kar_dir:
            return
        kar_out = self.validate_input(self.kar_out_entry, "Please enter the output KAR file name.")
        if not kar_out:
            return
        self.status_bar.config(text="Running Kar...")
        cmd = ["kar", "create", "-o", kar_out, kar_dir]
        self.run_command(cmd, self.kar_output)

# --------------------------------------------------------------------
# Main Application Entry Point
# --------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SraToolkitGUI(root)
    try:
        subprocess.run(["vdb-config", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        messagebox.showerror("Error", "SRA Toolkit not found. Please ensure it's installed and in your PATH.")
        root.destroy()
        sys.exit(1)
    root.mainloop()
