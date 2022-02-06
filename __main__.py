#!/usr/bin/env python3.8

ADDON_API_FSTRING = "https://addons-ecs.forgesvc.net/api/v2/addon/{}"

from argparse import ArgumentParser, FileType, ArgumentTypeError
from logging import DEBUG, INFO, WARNING, ERROR, basicConfig as logConfig
from pathlib import Path
from html.parser import HTMLParser
from json import load as jload
from urllib import request
from urllib.parse import quote

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
    with open(args.manifest, "r") as manifest_file:
        manifest = jload(manifest_file)

        for entry in manifest["files"]:
            project_id = entry["projectID"]
            response = request.urlopen(ADDON_API_FSTRING.format(project_id), timeout=60)
            content = jload(response)
            file_url = content["latestFiles"][-1]["downloadUrl"]

            download = request.urlopen(quote(file_url, safe=':/'))
            meta = download.info()
            file_name = file_url.split('/')[-1]
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
