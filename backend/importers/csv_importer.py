"""
CSV Importer Module
Handles importing and merging existing CSV files with newly scraped job data
"""

import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple
import ftfy


def normalize_text(value):
    """Normalize text by fixing encoding issues and whitespace"""
    if not isinstance(value, str) or pd.isna(value):
        return ""
    
    value = ftfy.fix_text(value)
    return " ".join(value.split())


def load_csv_file(file_path: str) -> List[Dict]:
    """
    Load job data from a CSV file
    
    Args:
        file_path: Path to the CSV file to import
        
    Returns:
        List of job dictionaries
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If the CSV is invalid or empty
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    if not path.suffix.lower() == '.csv':
        raise ValueError(f"File must be a CSV file, got: {path.suffix}")
    
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        if df.empty:
            raise ValueError("CSV file is empty")
        
        # Normalize text in all string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(normalize_text)
        
        # Convert to list of dictionaries
        jobs_data = df.to_dict('records')
        
        # Clean up the dictionaries - replace NaN with empty strings
        cleaned_jobs = []
        for job in jobs_data:
            cleaned_job = {}
            for key, value in job.items():
                if pd.isna(value):
                    cleaned_job[key] = ""
                else:
                    cleaned_job[key] = value
            cleaned_jobs.append(cleaned_job)
        
        return cleaned_jobs
        
    except pd.errors.EmptyDataError:
        raise ValueError("CSV file is empty or invalid")
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {str(e)}")


def merge_job_data(existing_jobs: List[Dict], new_jobs: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Merge existing job data with new job data
    
    This function appends the newly scraped jobs to the existing jobs from the CSV file.
    The order will be: existing jobs first, then new jobs.
    
    Args:
        existing_jobs: List of jobs from imported CSV
        new_jobs: List of jobs from current scraping session
        
    Returns:
        Tuple of (combined_jobs_list, count_of_jobs_from_csv)
    """
    # Combine both datasets - existing jobs first, then new jobs
    combined_jobs = existing_jobs + new_jobs
    
    # Return combined data and count of existing jobs
    return combined_jobs, len(existing_jobs)


def import_and_merge_csv(
    file_path: str, 
    current_jobs: List[Dict]
) -> Tuple[List[Dict], int]:
    """
    Main function to import CSV and merge with current job data
    
    This function allows you to append newly scraped data to an existing CSV file.
    The existing CSV data will be loaded first, then the current scraped jobs will be appended.
    
    Args:
        file_path: Path to the CSV file to import
        current_jobs: Current scraped job data (today's scrape)
        
    Returns:
        Tuple of (merged_jobs, imported_count)
        - merged_jobs: Combined list of all jobs (existing + new)
        - imported_count: Number of jobs imported from CSV
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV is invalid
        
    Example:
        >>> # Import existing data and add today's scrape
        >>> merged_jobs, imported_count = import_and_merge_csv("previous_scrape.csv", todays_jobs)
        >>> print(f"Imported {imported_count} existing jobs, added {len(todays_jobs)} new jobs")
    """
    # Load existing jobs from CSV
    existing_jobs = load_csv_file(file_path)
    
    # Merge with current jobs (existing first, then current)
    merged_jobs, imported_count = merge_job_data(existing_jobs, current_jobs)
    
    return merged_jobs, imported_count


def save_merged_data(merged_jobs: List[Dict], output_path: str) -> None:
    """
    Save merged job data to a CSV file
    
    This is a utility function to save the merged data back to a CSV file.
    
    Args:
        merged_jobs: Combined list of jobs
        output_path: Path where to save the merged CSV
        
    Raises:
        ValueError: If merged_jobs is empty
        IOError: If there's an error writing the file
    """
    if not merged_jobs:
        raise ValueError("No data to save - merged_jobs is empty")
    
    try:
        df = pd.DataFrame(merged_jobs)
        df.to_csv(output_path, index=False)
        print(f"✅ Saved merged data to: {output_path}")
        print(f"   Total jobs saved: {len(merged_jobs)}")
    except Exception as e:
        raise IOError(f"Error saving merged data: {str(e)}")