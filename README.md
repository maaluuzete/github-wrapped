# GitHub Wrapped CLI
A command-line interface tool designed to generate a retrospective report of any public GitHub user's activity. Using the GitHub REST API and the Rich library, this script transforms raw data into a visually organized dashboard directly in your terminal.
This tool fetches a user's public events over a specified period and calculates key statistics such as total commits, opened pull requests, merged pull requests, and created issues. It also analyzes the user's repositories to determine their primary programming languages and identifies their most active repositories and busiest days.

## Project Structure
The project consists of the following files located in a single directory:
```
github-wrapped/
├── LICENSE
├── README.md
├── main.py
└── requirements.txt
```
## Features
* Activity Summary: Calculation of commits, PRs (opened and merged), and issues;
* Top Repositories: Identification of the top 5 most active repositories based on event count;
* Language Analysis: Summary of programming languages used across the user's repositories;
* Busiest Day: Detection of the date with the highest number of recorded events;
* Smart Pagination: Automatic fetching of multiple pages of data until the specified time window is met.

## Installation
To use this tool, you must have a GitHub Personal Access Token (PAT).
1. Navigate to GitHub Settings > Developer Settings > Personal access tokens > Tokens (classic).
2. Generate a new token. No specific scopes are required for accessing public data.
3. Keep the token secure as it will be used for API authentication.

Clone or download the project files into a single folder.

1. Install the required dependencies using pip: ```pip install -r requirements.txt```
2. Create a file named .env in the root directory.
3. Add your GitHub token to the .env file:```GITHUB_TOKEN=your_personal_access_token_here```

Run the script from your terminal by providing the target username and the number of days for the report:

```python main.py --username "github-username" --days DAY```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.