"""
Parses a DDL and generate a Talend XML file that can be imported into Talend schema metadata.
"""
import sys

"""
Logic

Read SQL from input file per line
Convert SQL to a single line by removing all new lines (even if file is already single line)
Separate each section of the SQL, by ',' into a list
Separate the column declarations into a list
Determine Column Name, Data Type and Size (if provided) and store in a nested list
Generate XML and output to a file
Generate a report that contains any issue or warnings that were encountered such as unknown data types,
    missing size for data types that require a size (Varchar, Char, Decimal, etc), and possible edge cases
    that could not be handled.
"""
# TODO - Complete the dictionary of Teradata types to Talend Types
# TODO - Add DDL error handling (invalid data types, missing column size, etc.)

# A dictionary of valida data types and their Talend counterpart
talend_type = {
    "CHAR": "id_String",
    "VARCHAR": "id_String",
    "CLOB": "id_String",
    "JSON": "id_String",
    "SMALLINT": "id_Integer",
    "INTEGER": "id_Integer",
    "BIGINT": "id_Integer",
    "DECIMAL": "id_Float",
    "DATE": "id_Date",
    "TIMESTAMP": "id_String"
}


def get_column_type_size(column_data):
    """
    Gets the column data type and size, if applicable, and returns the values in a list.
    :param column_data: <string> The column type and size.
    :return: A list containing the column data type and size, if applicable.
    """

    # Separate the column size from the data type
    column_type_size = column_data.replace(')', '')
    column_type_size = column_type_size.split('(')

    # Return the list containing the column type and the size
    return column_type_size


def generate_xml(column_list, xml_file):
    """
    Generate XML for Talend based on the column names and data types provided. Must be in a list format
    [COL_NAME, DATA_TYPE_SIZE].
    :param column_list: A list of column names and data types.
    :param xml_file: The path to the XML output file.
    :return: Status of XML generation.
    """

    try:
        # Open output file for writing
        with open(xml_file, 'w+') as output_file:
            # Write header lines
            output_file.write('<?XML version="1.0" encoding="UTF-8"?>')
            output_file.write('<schema dbmsId="teradata">')

            # For each column in list; Get column name, data type, and size
            for column in column_list:

                # Validate column contains at least 2 elements
                if len(column) < 2:
                    # Print data of invalid column definition and return
                    print(f"Unable to parse column data: {column}")
                    print("The column data is invalid. The column should contain at least 2 elements.")
                    print("[<COLUMN_NAME>, <DATA_TYPE>]")
                    exit(1)

                # Get column name
                column_name = column[0]

                # Get the column data type and size
                column_details = get_column_type_size(column[1])

                # Get column type
                column_type = column_details[0]

                # Validate column data type against dictionary
                try:
                    talend_type[column_type]
                except KeyError:
                    print(f"Data Type: {column_type} is a not a valid data type.")
                    exit(1)

                # Get column size and precision based on data type
                if column_type in ['DECIMAL']:
                    # Get column size
                    column_size = ''
                    column_precision = column_details[1].split(',')[1]
                else:
                    # Get column size
                    if len(column_details) > 1:
                        column_size = column_details[1]
                    else:
                        column_size = ''

                    column_precision = ''

                # Generate the XML
                output_file.write(f'<column comment="" default="" key="false" label="{column_name}" '
                                  f'length="{column_size}" nullable="true" originalDbColumnName="{column_name}" '
                                  f'pattern="" precision="{column_precision}" talendType="{talend_type[column_type]}" '
                                  f'type="{column_type}"/>')

            # Write closing line
            output_file.write('</schema>')

            # Close the output file
            output_file.close()

    except Exception as e:
        print(e)
        exit(1)

    return 'Done'


def parse_columns(ddl_data):
    """
    Parse the columns from the provided DDL data and return a nested list of column names, data types, and size.

    :param ddl_data: A string that contains the DDL from a SQL file.
    :return: A nested list of column names, data types, and size.
    """
    # Local Variables
    section_index = 0
    column_section = []
    column_list = []

    # Split the ddl into multiple sections based on comma.
    ddl_sections = ddl_data.split(',')

    # Get the index of the first column definition
    for section_index in range(len(ddl_sections)):
        # Strip extra spacing from line
        section = ddl_sections[section_index].strip()

        # In order to determine where the column list begins, check for a single occurrence of '(' without a closing ')'
        if '(' in section and ')' not in section:
            break  # Once starting index is found, exit loop

    # Loop the the column section of the DDL and store columns in list
    for column_index in range(section_index, len(ddl_sections)):
        # Check for the end of the column section and break
        # The column section should always be succeeded by CONSTRAINT PRIMARY KEY, UNIQUE INDEX, and or ');'
        if all(keyword in ddl_sections[column_index] for keyword in ("CONSTRAINT", "PRIMARY KEY")):
            break  # Stop if end of column section is encountered
        elif all(keyword in ddl_sections[column_index] for keyword in "UNIQUE INDEX"):
            break  # Stop if end of column section is encountered
        else:
            # Add column section to column list after strip extra spaces
            column_section.append(ddl_sections[column_index].strip())

    # Edge Case: Sometimes the first column may be preceded by a MAP attribute that needs to be removed
    column_section[0] = str.strip(column_section[0].partition('(')[-1])

    # The skip index flag is used to skip indexes in the list if current list item was merged with next list item.
    # This is needed because Python is too smart for its own good and does not allow incrementing the index inside loop.
    # Example:  Current List Item = 'DECIMAL(9'
    #           Next List Item = '2)'
    # Both lines are incomplete and need to be merged to form a valid column definition
    skip_index = False

    for column_index in range(len(column_section)):
        if not skip_index:
            # For Decimal columns, the size may be separated on two lines and will need to be merged
            if all(keyword in column_section[column_index] for keyword in ("DECIMAL", "(")) \
                    and ")" not in column_section[column_index]:
                # Merge the two lines for the decimal, and then split each section of the column definition
                column_details = (column_section[column_index] + ',' + column_section[column_index+1]).split(' ')
                # Append only the column name and data type to the column list
                column_list.append([column_details[0], column_details[1]])
                # Skip over the next index, since it was merged with the current list item.
                skip_index = True
            else:
                # Split each section of the column definition
                column_details = column_section[column_index].split(' ')
                # Append only the column name and data type to the column list.
                # The column name and data type will always be the first to elements.
                column_list.append([column_details[0], column_details[1]])
        else:
            # Reset skip index flag
            skip_index = False

    return column_list


def read_ddl(ddl_file):
    """
    Reads a DDL from the specified file and returns in as a string.
    :param ddl_file: The path to a file that contains the DDL to parse
    :return: <String> The DDL that was read from the specified file
    """

    # Open input and output files for reading and writing
    ddl = ""

    try:
        with open(ddl_file, 'r') as input_file:
            # Read all lines from DDL file and then combine into single line
            # This allows for the DDL file to be formatted with a single line or multiple lines
            for line in input_file.read():
                ddl += line.replace("\n", "")

        # Close the SQL file
        input_file.close()

        return ddl

    except Exception as readException:
        print(readException)
        exit(1)


if __name__ == '__main__':

    # Validate input parameters
    if len(sys.argv) < 3:
        print("Required parameters missing!")
        print("Usage: DDLtoXML.py <input_ddl_file_path> <output_xml_file_path")
        exit(1)

    print("Parsing parameters...")

    # Set the input ddl file path
    input_ddl = sys.argv[1]

    # Set the output xml file path
    output_xml = sys.argv[2]

    print(f"Reading from input file {input_ddl}...")

    # Get the DDL data from a file
    ddl_data = read_ddl(input_ddl)
    print("Input file read successfully!")

    # Get the column data from the DDL data
    print("Fetching column data from DDL...")
    column_list = parse_columns(ddl_data)
    print(column_list)
    print("Column listed successfully created!")

    # Generate the XML data
    print(f"Generate XML and writing the data to {output_xml}...")
    status = generate_xml(column_list, output_xml)

    if status == 'Done':
        print("The XML file was created successfully.")
    else:
        print("Unable to create the XML output! See logs for more details.")
