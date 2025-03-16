import os
import sys
import argparse
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from colorama import init, Fore, Style

init(autoreset=True)


def clearScreen():
    os.system("cls" if os.name == "nt" else "clear")


def printBanner():
    clearScreen()
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}==========================================
       downloadSite.py
==========================================
    """
    print(banner)


def parseArguments():
    parser = argparse.ArgumentParser(
        description="Download all files from a web folder."
    )
    parser.add_argument(
        "folderUrl",
        help="The URL of the web folder to download files from (e.g., http://example.com/files/)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output directory (default: current directory)",
        default=os.path.expanduser("~/Downloads/downloadSite/"),
        # "~/Downloads/downloadSite/",
    )
    return parser.parse_args()


def getFileLinks(folderUrl):
    """Fetch the folder listing page and extract file links."""
    try:
        response = requests.get(folderUrl)
        response.raise_for_status()
    except Exception as e:
        print(f"{Fore.RED}Error accessing {folderUrl}: {e}")
        sys.exit(1)
    soup = BeautifulSoup(response.text, "html.parser")
    links = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href or href in ["../", "./"] or "O=" in href:
            continue
        fullUrl = urljoin(folderUrl, href)
        if href.endswith("/"):
            print(f"{Fore.YELLOW}Skipping directory: {fullUrl}")
            continue
        links.append(fullUrl)
    if not links:
        print(f"{Fore.YELLOW}No downloadable file links found at {folderUrl}.")
        sys.exit(0)
    return links


def downloadFile(url, outputDir):
    localFilename = os.path.join(outputDir, os.path.basename(urlparse(url).path))
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            totalSize = int(r.headers.get("content-length", 0))
            blockSize = 1024
            t = tqdm(
                total=totalSize,
                unit="iB",
                unit_scale=True,
                desc=f"Downloading {os.path.basename(url)}",
                leave=False,
            )
            with open(localFilename, "wb") as f:
                for data in r.iter_content(blockSize):
                    t.update(len(data))
                    f.write(data)
            t.close()
            if totalSize != 0 and t.n != totalSize:
                print(f"{Fore.RED}ERROR, something went wrong downloading {url}")
    except Exception as e:
        print(f"{Fore.RED}Failed to download {url}: {e}")
        return False
    return True


def main():
    printBanner()
    args = parseArguments()
    if not os.path.isdir(args.output):
        try:
            os.makedirs(args.output)
            print(f"{Fore.GREEN}Created output directory: {args.output}")
        except Exception as e:
            print(f"{Fore.RED}Error creating directory {args.output}: {e}")
            sys.exit(1)
    print(f"{Fore.YELLOW}Scanning for files in: {args.folderUrl}")
    fileLinks = getFileLinks(args.folderUrl)
    print(f"{Fore.GREEN}Found {len(fileLinks)} file(s) to download.\n")
    for fileUrl in fileLinks:
        print(f"{Fore.CYAN}Starting download: {fileUrl} to {args.output}")
        success = downloadFile(fileUrl, args.output or "~/Downloads/downloadSite/")
        if success:
            print(f"{Fore.GREEN}Downloaded successfully: {os.path.basename(fileUrl)}\n")
        else:
            print(f"{Fore.RED}Download failed for: {fileUrl}\n")
    print(f"{Fore.MAGENTA}{Style.BRIGHT}All downloads completed.")


if __name__ == "__main__":
    main()
