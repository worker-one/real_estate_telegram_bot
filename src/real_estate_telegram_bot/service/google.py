import io
import json
import logging
import os.path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_keyfile_dict() -> dict[str, str]:
    """ Create a dictionary with keys for the Google Sheets API from environment variables

    Returns:
        Dictionary with keys for the Google Sheets API
    Raises:
        ValueError: If any of the environment variables is not set
    """
    variables_keys = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY").replace('\\n', '\n'),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }
    for key in variables_keys:
        if variables_keys[key] is None:
            raise ValueError(f"Environment variable {key} is not set")
    return variables_keys


class GoogleDriveAPI:
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    SERVICE_ACCOUNT_FILE = './src/real_estate_telegram_bot/conf/credentials.json'

    def __init__(self):
        try:
            self.keyfile_dict = json.load(open(self.SERVICE_ACCOUNT_FILE))
        except FileNotFoundError:
            logger.info("Credentials json file has not been found. Using environment variables instead.")
            self.keyfile_dict = create_keyfile_dict()
        self.credentials = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict=self.keyfile_dict, scopes=self.SCOPES)
        self.service = build("drive", "v3", credentials=self.credentials)

        self.file_index = {}
        self._file_index = {}

        self.dir_index = {}
        self._dir_index = {}

    def upload_file(self, file_path: str, mime_type: str) -> None:
        try:
            file_metadata = {'name': os.path.basename(file_path)}
            media = MediaFileUpload(file_path, mimetype=mime_type)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            logger.info(f"File ID: {file.get('id')}")
        except HttpError as error:
            logger.error(f"An error occurred: {error}")

    def download_file(self, file_id: str, destination: str) -> None:
        """Downloads a file from Google Drive.
        Args:
            file_id: ID of the file to download.
            destination: Path to save the downloaded file.
        """
        try:
            request = self.service.files().get_media(fileId=file_id)
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                logger.info(f"Download {int(status.progress() * 100)}%.")

            with open(destination, 'wb') as f:
                f.write(file.getvalue())
            logger.info(f"File downloaded to {destination}")
        except HttpError as error:
            logger.info(f"An error occurred: {error}")

    def find_file_id(self, file_name: str) -> str:
        """Searches for a file by name and returns its ID.
        Args:
            file_name: Name of the file to search for.
        Returns:
            The ID of the file if found, None otherwise.
        """
        try:
            files = []
            page_token = None
            while True:
                response = (
                    self.service.files()
                    .list(
                        q=f"name='{file_name}'",
                        spaces="drive",
                        fields="nextPageToken, files(id, name)",
                        pageToken=page_token,
                    )
                    .execute()
                )
                for file in response.get("files", []):
                    logger.info(f'Found file: {file.get("name")}, {file.get("id")}')
                files.extend(response.get("files", []))
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break

            if not files:
                logger.info("No files found.")
                return None
            return files[0]['id']
        except HttpError as error:
            logger.info(f"An error occurred: {error}")
            return None

    def get_folder_name(self, folder_id: str) -> str:
      """Gets the folder name by its ID.
      Args:
          folder_id: ID of the folder.
      Returns:
          The name of the folder.
      """
      try:
          folder = self.service.files().get(fileId=folder_id, fields='name').execute()
          return folder.get('name')
      except HttpError as error:
          logger.info(f"An error occurred: {error}")
          return "Unknown"

    def search(self, query: str, case_sensitive: bool = True) -> list[dict]:
      if case_sensitive:
        return self.dir_index.get(query, [])
      else:
        return self._dir_index.get(query.lower().strip(), [])

    def index(self) -> None:
        """Indexes all files in Google Drive and saves their names and directories as attributes."""
        try:
            new_files_count = 0
            page_token = None
            while True:
                response = (
                    self.service.files()
                    .list(
                        spaces="drive",
                        fields="nextPageToken, files(id, name, parents)",
                        pageToken=page_token,
                    )
                    .execute()
                )
                for file in response.get("files", []):
                    if file["id"] not in self.file_index.values():
                        parent_id = file.get('parents', [None])[0]
                        parent_name = self.get_folder_name(parent_id) if parent_id else "Root"

                        # Update file_index
                        self.file_index[file['name']] = {'id': file.get("id"), 'parent_name': parent_name}

                        # Update dir_index
                        if parent_name not in self.dir_index:
                            self.dir_index[parent_name] = []
                            self._dir_index[parent_name.lower().strip()] = []

                        self.dir_index[parent_name].append({'file_name': file['name'], 'id': file['id']})
                        self._dir_index[parent_name.lower().strip()].append({'file_name': file['name'], 'id': file['id']})

                        new_files_count += 1
                page_token = response.get("nextPageToken", None)
                if page_token is None:
                    break
            logger.info(f"New files have been indexed: {new_files_count}")
        except HttpError as error:
            logger.info(f"An error occurred: {error}")
            logger.info(f"Indexed directories {len(self.dir_index.keys())}.")
        # Save the index to a file json
        with open('./src/real_estate_telegram_bot/conf/google_drive_index.json', 'w') as f:
            json.dump(self.dir_index, f)

    def load_index(self) -> None:
        try:
            with open('./src/real_estate_telegram_bot/conf/google_drive_index.json', 'r') as f:
                logger.info("Loading index file.")
                self.dir_index = json.load(f)
                for parent_name, files in self.dir_index.items():
                    self._dir_index[parent_name.lower().strip()] = files
        except FileNotFoundError:
            logger.info("Index file has not been found. Indexing files.")
            self.index()
        except json.JSONDecodeError:
            logger.info("Index file is empty. Indexing files.")
            self.index()
