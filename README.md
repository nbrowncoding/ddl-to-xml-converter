# Teradata DDL to Talend XML Converter

A simple python scipt that takes a Teradata DDL and converts the DDL into an XML format that can be imported as metadata into Talend Open Studio. I created project to save time when attempting to build large table schemas in Talend. Since manually adding and defining columns took too long, I wrote this program to automatically do it for me.

## Supported Software Versions
Teradata 16.20+
<br/>
Talend Open Studio 7.0+
<br/>
Python 3.6+

## Planned Future Updates
* Additional database type support (SQL, MySQL, Oracle, etc)
* Additional support for dates and formats
* Support for primary keys
* Support for NOT NULL column
* Warning/Error logging and reporting

## Additional Notes
The Teradata data type to Talend data type is setup for my own personal perference and may need to be adjusted to fit your needs. I tried to make this a one size fits all solution, but there may be some edge cases that are not handled currently. Feel free to suggest any edge cases and I can work on adding support for them. I will not be allowing pull requests at this time, so please fork the project and make any changes you see fit.
