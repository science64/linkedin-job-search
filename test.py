import re

with open("./files/links.txt", "r") as file:
    existing_links = set(line.strip() for line in file.readlines())

# Regular expression pattern to extract job ID
pattern = re.compile(r"/jobs/view/[^/]+-(\d+)\??")

# Extract and print job IDs
for url in existing_links:
    match = pattern.search(url)
    if match:
        job_id = match.group(1)
        print(job_id)
    else:
        print("No match")