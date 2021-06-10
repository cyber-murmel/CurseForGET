#!/usr/bin/env python3.8

from argparse import ArgumentParser, FileType, ArgumentTypeError
from logging import DEBUG, INFO, WARNING, ERROR, basicConfig as logConfig
from pathlib import Path
from html.parser import HTMLParser
from json import load as jload
from urllib import request

def parse_arguments():
    def file_path(path):
        p = Path(path)
        if p.is_file():
            return path
        else:
            raise ArgumentTypeError(f"{path} is not a file.")
    def dir_path(path):
        p = Path(path)
        if p.is_dir():
            return path
        else:
            raise ArgumentTypeError(f"{path} is not a file.")

    parser = ArgumentParser(description="Get all the mods", epilog="")

    verbose = parser.add_mutually_exclusive_group()
    verbose.add_argument("-q", "--quiet",   action="store_true", help="turn off warnings")
    verbose.add_argument("-v", "--verbose", action="count",      help="set verbose loglevel")

    parser.add_argument("--modlist", type=file_path, required=True)
    parser.add_argument("--manifest", type=file_path, required=True)
    parser.add_argument("--directory", type=dir_path, required=True)

    args = parser.parse_args()
    return args

class MyHTMLParser(HTMLParser):
    urls = list()

    def handle_starttag(self, tag, attrs):
        if "a" == tag:
            self.urls += [attrs[0][1]]

def get_log_level(verbose, quiet):
        return  ERROR   if quiet else \
                WARNING if not verbose else \
                INFO    if 1 == verbose else \
                DEBUG   #  2 <= verbose

def main(args):
    log_level = get_log_level(args.verbose, args.quiet)
    modlist_parser = MyHTMLParser()
    with open(args.modlist, "r") as modlist_file, open(args.manifest, "r") as manifest_file:
        modlist_parser.feed(modlist_file.read())
        modlist_urls = modlist_parser.urls
        manifest = jload(manifest_file)
        file_ids = [entry["fileID"] for entry in manifest["files"]]
        download_urls = [f"{url}/download/{fid}/file" for url, fid in zip(modlist_urls, file_ids)]
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Upgrade-Insecure-Requests": "1"
        }
        for url in download_urls:
            req = request.Request(url, None, headers)
            response = request.urlopen(req)
            file_url = response.url
            file_name = file_url.split('/')[-1]

            download = request.urlopen(file_url)
            meta = download.info()
            file_size = int(meta.get("Content-Length"))
            print(f"Downloading: {file_name} Bytes: {file_size}")

            file_size_dl = 0
            block_sz = 8192
            with open(f"{args.directory}/{file_name}", "wb") as f:
                while True:
                    buffer = download.read(block_sz)
                    if not buffer:
                        break

                    file_size_dl += len(buffer)
                    f.write(buffer)
                    status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                    status = status + chr(8)*(len(status)+1)
                    print(status, end = "")



if "__main__" == __name__:
    args = parse_arguments()
    main(args)
