import os
import sys
import urllib.request as request
from urllib.request import urlopen
from urllib.parse import unquote, urlparse
from urllib.error import HTTPError
import zipfile
from mlcore import logger
from mlcore.utils.common import get_size
from pathlib import Path
from mlcore.entity.config_entity import DataIngestionConfig
from tempfile import NamedTemporaryFile

CHUNK_SIZE = 40960


class DataIngestion:
    def __init__(self, config: DataIngestionConfig):
        self.config = config

    def download_data(self):
        if len(os.listdir(self.config.local_data_path)) == 0:
            directory, download_url_encoded = self.config.source_URL.split(":")
            download_url = unquote(download_url_encoded)
            filename = urlparse(download_url).path
            destination_path = os.path.join(self.config.root_dir, directory)
            try:
                with urlopen(download_url) as fileres, NamedTemporaryFile() as tfile:
                    total_length = fileres.headers["content-length"]
                    logger.info(
                        f"Downloading {directory}, {total_length} bytes compressed"
                    )
                    dl = 0
                    data = fileres.read(CHUNK_SIZE)
                    while len(data) > 0:
                        dl += len(data)
                        tfile.write(data)
                        done = int(50 * dl / int(total_length))
                        sys.stdout.write(
                            f"\r[{'=' * done}{' ' * (50-done)}] {dl} bytes downloaded"
                        )
                        sys.stdout.flush()
                        data = fileres.read(CHUNK_SIZE)
                    logger.info("\n")
                    if filename.endswith(".zip"):
                        logger.info(f"Uncompressing {filename}")
                        with zipfile.ZipFile(tfile) as zfile:
                            zfile.extractall(destination_path)

                    else:
                        logger.info(f"Uncompressing {filename}")
                        with tarfile.open(tfile.name) as tarfile:
                            tarfile.extractall(destination_path)
                    logger.info(f"Downloaded and uncompressed: {directory}")
            except HTTPError as e:
                logger.error(
                    f"Failed to load (likely expired) {download_url} to path {destination_path}"
                )
            except OSError as e:
                logger.error(
                    f"Failed to load {download_url} to path {destination_path}"
                )
        else:
            logger.info(
                f"Data already exists in location {self.config.local_data_path}, skipping download!"
            )