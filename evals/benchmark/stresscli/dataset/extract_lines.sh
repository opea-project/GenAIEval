#!/bin/bash

# Check for the correct number of arguments
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 input_file output_file begin_id end_id"
    exit 1
fi

input_file="$1"
output_file="$2"
begin_id="$3"
end_id="$4"

# Create or clear the output file
> "$output_file"

# Initialize a flag to indicate whether we have started writing
writing=false

# Read through the input file line by line
while IFS= read -r line; do
    # Check if the line is valid JSON and extract the ID
    if echo "$line" | jq -e . >/dev/null 2>&1; then
        # Extract the ID from the JSON object
        id=$(echo "$line" | jq -r .id)

        # Check if we have reached the beginning ID
        if [[ "$id" == "$begin_id" ]]; then
            echo "$line" >> "$output_file"
            writing=true  # Start writing after finding begin_id
            continue       # Continue to next line after writing begin_id
        fi

        # If we have started writing, keep writing until we reach end_id
        if [[ "$writing" == true ]]; then
            echo "$line" >> "$output_file"
        fi

        # Stop processing if we reach end_id
        if [[ "$id" == "$end_id" ]]; then
            break  # Stop after writing end_id, do not write again
        fi
    fi
done < "$input_file"

echo "Records from ID $begin_id to $end_id have been extracted to $output_file."