import os, sys, requests
from zipfile import ZipFile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utility.utility import setup_logging


def download_zip_file(logger, url, output_dir):
    response = requests.get(url, stream=True)
    os.makedirs(output_dir, exist_ok=True)

    if response.status_code == 200:
        filename = os.path.join(output_dir, "downloaded.zip")
        with open(filename, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info(f"Downloaded zip file: {filename}")
        return filename
    else:
        raise Exception(f"Failed to download file: Status code {response.status_code}")


def extract_zip_file(logger, zip_filename, output_dir):

    with ZipFile(zip_filename, "r") as zip_file:
        zip_file.extractall(output_dir)

    logger.info(f"Extract files written to: {output_dir}")
    logger.info("Removing the zip file")
    os.remove(zip_filename)

if __name__ == "__main__":
    logger = setup_logging("extract.log")

    if len(sys.argv) < 2:
        logger.info("Extraction path is required")
        logger.info("Exame Usage:")
        logger.info("python3 execute.py /home/Data/Extraction")
    else:
        try:
            logger.info("Starting Extration Engine...")
            EXTRACT_PATH = sys.argv[1]
            KAGGLE_URL = "https://storage.googleapis.com/kaggle-data-sets/7774671/12333656/bundle/archive.zip?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20250816%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20250816T191250Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=ab96c36af10f8d5fc8932677a74e58f338709174e0fb748b8c05456973e0b7a0bc202d8c12dd12d35529af6f9778aa0856c06a97b0db7f23105619948fb9ce50cb30e619b416cbefe8cd9c712efa018cc88496cdcccda3d07208ac52ade72f8caec035014f62c456a07130103bd973c8c905a5aa255b5e560ecfb0f9e096468cb43d36eccfb3bf94f156250825c30a51ab592886927521db9f63b1451d6e8f340e5975ff987919e3f3e749ac40dd67d394390bf748c2afc46fa3c8ccb32682b4ab57f54f93ec1a7bcefebd69dc9c4386c09df609005fdbd7dbf4ce73cbe2a8b741fec3ccd6ed10b7bd8ffdf2e860b6aef976af7fa2cfe51d301574ac304a2639"
            zip_filename = download_zip_file(logger, KAGGLE_URL, EXTRACT_PATH)
            extract_zip_file(logger, zip_filename, EXTRACT_PATH)
            logger.info("Extraction Successfully Completed!! :))")
        except Exception as e:
            logger.error(f"Error: {e}")
