#!/bin/bash

# Convert description/manual page document to C source file
# arg1 - document file path

document_path=$1
document_file_name=$(basename "${document_path}")
document_name=$(basename -s ".doc" "${document_file_name}")
source_file_name="${document_name}.txt.c"

rm -f "${source_file_name}"
#echo "Generating ${source_file_name}"
echo "static const char *txt =" >> "${source_file_name}"
sed 's/"/\\"/g; s/.*/    "&\\n"/' "${document_file_name}" >> "${source_file_name}"
echo ";" >> ${source_file_name}
echo "const char *${document_name}(void)" >> "${source_file_name}"
echo "{" >> "${source_file_name}"
echo "  return txt;" >> "${source_file_name}"
echo "}" >> "${source_file_name}"
 
