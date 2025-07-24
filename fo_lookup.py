import streamlit as st
import pandas as pd
import re

@st.cache_data
def load_data(file_path):
    """Loads the data from a CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except FileNotFoundError:
        st.error(f"Error: The file '{file_path}' was not found. Please make sure the file is in the correct directory.")
        return None
    except Exception as e:
        st.error(f"An error occurred while loading the data: {e}")
        return None


def search_citable_reference(text_string, dataframe):
    """
    Extracts digits after the last '/' and between the first and second '/',
    formats the code digits as 'Code XX', searches 'description' column using a precise regex,
    extracts file number ranges from the description, filters based on file number,
    and returns a table of 'citable reference' and 'description' for matching rows.
    """
    try:
        # Split the text_string by '/'
        parts = text_string.split('/')

        # Check if there are enough parts
        if len(parts) < 2:
            return "Error: The text string must contain at least one '/'."

        # Extract digits after the last '/'
        code_digits = parts[-1]
        if not code_digits.isdigit():
            return "Error: The text after the last '/' is not a digit."

        # Extract digits between the first and second '/'
        if len(parts) > 1:
            file_digits_str = parts[1]
            if not file_digits_str.isdigit():
                return "Error: The text between the first and second '/' is not a digit."
            file_digits = int(file_digits_str)
        else:
            return "Error: The text string must contain at least two '/' to extract digits between the first and second '/'."


        # Format the search string using regex for precise matching
        search_string_regex = rf"Code {code_digits}\b" # Use \b to match word boundary

        # Search for the string in the 'Description' column using regex
        result_rows = dataframe[dataframe['Description'].str.contains(search_string_regex, na=False, regex=True)].copy()

        # Exclude "Code 126" but include "Code 12" by checking if the code digits are exactly '126'
        if code_digits == '126':
             return "Search for 'Code 126' is excluded."


        # Extract and parse file number ranges from 'Description'
        def extract_file_range(description):
            if pd.isna(description):
                return None
            # Regex to find patterns like "Files XX - YY" or "File ZZ"
            match_range = re.search(r"Files\s+(\d+)\s*-\s*(\d+)", description)
            if match_range:
                return (int(match_range.group(1)), int(match_range.group(2)))

            match_single = re.search(r"File\s+(\d+)", description)
            if match_single:
                num = int(match_single.group(1))
                return (num, num) # Represent a single file as a range (num, num)
            return None # No file range found

        result_rows['File_Range'] = result_rows['Description'].apply(extract_file_range)

        # Filter based on file range
        # Ensure 'File_Range' is not None and file_digits is within the range
        result_rows = result_rows[result_rows['File_Range'].apply(
            lambda x: x is not None and x[0] <= file_digits <= x[1]
        )]

        # Remove the temporary 'File_Range' column
        result_rows = result_rows[['Citable Reference', 'Description']]

        # Return the 'Citable Reference' and 'Description' for all matching rows
        if not result_rows.empty:
            return result_rows
        else:
            return f"No match found for 'Code {code_digits}' with file {file_digits} in the description."

    except Exception as e:
        return f"An error occurred: {e}"


def main():
    """Defines the layout and flow of the Streamlit app."""
    st.title("FO Correspondence Discovery Search")
    st.write("Enter a text string with '/' to search for corresponding records in the FO correspondence data.")

    # Load the data using the cached function
    csv_file_path = "FO correspondence discovery download 1920-25.csv"
    df = load_data(csv_file_path)

    if df is not None: # Only proceed if data loaded successfully
        user_input = st.text_input("Please enter a text string containing a '/':")

        if user_input: # Only perform search if user_input is not empty
            result = search_citable_reference(user_input, df)

            if isinstance(result, pd.DataFrame):
                st.dataframe(result)
            else:
                st.write(result)


if __name__ == "__main__":
    main()
