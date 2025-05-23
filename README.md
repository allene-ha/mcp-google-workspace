# Google Workspace MCP Server

An integrated MCP (Model Context Protocol) server supporting Google Sheets, Google Docs, and Google Drive.

## 🚀 Key Features

### Google Sheets
- 📊 **Read/Write Data**: Read and update data from spreadsheets.
- 📝 **Sheet Management**: List sheets, create new spreadsheets.

### Google Docs
- 📖 **Read Document**: Retrieve document content in text, JSON, or Markdown format.
- ✍️ **Text Editing**: Append, insert, and delete text.
- 🎨 **Formatting**: Apply text formatting like bold, italics, color, and font.
- 📋 **Structural Elements**: Insert tables and page breaks.

### Google Drive
- 📂 **List Spreadsheets**: List spreadsheets from a specific Google Drive folder or the entire Drive (`list_spreadsheets`).
- 🔍 **Search Workspace Files**: Search for Sheets/Docs files within a specific Google Drive folder or the entire Drive (`search_workspace_files`).

### Other Server Features
- ℹ️ **Status Information**: Check connection status and available tools (`get_workspace_info`).

## 📦 Installation

This project can be installed for local development and testing as follows:

1.  **Clone Repository**:
    ```bash
    git clone <REPOSITORY_URL>
    cd mcp-google-workspace
    ```

2.  **Create and Activate Virtual Environment (Recommended)**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # macOS/Linux
    # .venv\Scripts\activate   # Windows
    ```

3.  **Install Dependencies and Project (Editable Mode)**:
    Use `uv` (recommended) or `pip` to install.
    ```bash
    # Using uv
    uv pip install -e .

    # Using pip
    pip install -e .
    ```
    The `-e .` option installs the project in "editable" mode, so changes to the source code are immediately reflected.

### Google API Setup

#### Google Cloud Console Configuration
1. Create a new project in the [Google Cloud Console](https://console.cloud.google.com/).
2. Enable the following APIs:
   - Google Sheets API
   - Google Docs API
   - Google Drive API

#### Create OAuth Credentials
1. Go to "APIs & Services" → "Credentials".
2. Click "Create Credentials" → "OAuth client ID".
3. Select Application type: "Desktop app".
4. Save the generated JSON file as `credentials.json` in the project root.

#### Configure OAuth Consent Screen
1. Go to "APIs & Services" → "OAuth consent screen".
2. Select User Type: "External".
3. Fill in the required information.
4. Add Scopes:
   - `https://www.googleapis.com/auth/spreadsheets`
   - `https://www.googleapis.com/auth/documents`
   - `https://www.googleapis.com/auth/drive.file`
5. Add your email to "Test users".

## 🔧 Usage

If the project is installed in editable mode (`-e .`), you can run the MCP server using the script defined in `pyproject.toml`:

```bash
# Run while the virtual environment is activated
mcp-google-workspace
```

Alternatively, you can run it as a Python module from the project root directory:

```bash
python -m src.mcp_google_workspace.server
```

### Using with Claude Desktop

Add the following configuration to your `mcp_config.json` file (the filename might vary, e.g., `mcp.json` or `mcp_servers.json` depending on your environment):

```json
{
  "mcpServers": {
    "google-workspace": {
      "command": "mcp-google-workspace",
      "env": {
        "CREDENTIALS_PATH": "/path/to/your/credentials.json",
        "TOKEN_PATH": "/path/to/your/token.json"
      }
    }
  }
}
```

### Environment Variables

- `CREDENTIALS_PATH`: Path to the OAuth credentials file (defaults to `credentials.json` in the workspace root).
- `TOKEN_PATH`: Path to the token storage file (defaults to `token.json` in the workspace root).
- `DRIVE_FOLDER_ID`: Specific Google Drive folder ID to work with (optional; if not specified, searches the entire Drive).

(Note: `SERVICE_ACCOUNT_PATH` is not used in this implementation as it currently uses the OAuth 2.0 user authentication flow.)

## 🛠️ Available Tools

A list of available tools grouped by functionality. You can also get the full dynamic list via `get_workspace_info`.

### Google Sheets Tools
- `get_sheet_data`: Retrieve sheet data.
- `update_cells`: Update cell data.
- `list_sheets`: List sheet names within a specific spreadsheet.
- `create_spreadsheet`: Create a new spreadsheet.

### Google Docs Tools
- `read_google_doc`: Read document content.
- `append_to_google_doc`: Append text to the end of a document.
- `insert_text`: Insert text at a specific location.
- `delete_range`: Delete content within a range.
- `apply_text_formatting`: Apply text formatting.
- `insert_table`: Insert a table.
- `insert_page_break`: Insert a page break.

### Google Drive Tools
- `list_spreadsheets`: List spreadsheets from Google Drive.
- `search_workspace_files`: Search for Sheets/Docs files in Google Drive.

### Other Server Tools
- `get_workspace_info`: Retrieve connection information and a dynamic list of all currently available tools.
- `simple_context_test`: (For development and testing) Test context accessibility.

## 💡 Example Usage

In Claude Desktop, you can use commands like:

```
"Show me a list of spreadsheets."
"Read the Google Doc with ID 'abc123'."
"Create a new spreadsheet titled 'Project Plan'."
"Add a bold heading 'Meeting Summary' to the document."
```

## 🔒 Security

- Keep your `credentials.json` and `token.json` files secure.
- Do not upload these files to public repositories.
- Ensure these credential files are included in your `.gitignore`.

## 🤝 Contributing

Feel free to raise issues or suggest improvements on GitHub!

## 📄 License

This project is distributed under the MIT License.

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 