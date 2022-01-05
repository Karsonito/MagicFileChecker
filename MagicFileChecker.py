#!/usr/bin/env python3
import magic
import mimetypes
import os
import sys
import argparse
import pprint

mimetypes.init()


parser = argparse.ArgumentParser(
    description="""
Magic file checker is a tool for mass checking structure of recovered files (from broken filesystem, backups, etc).
It uses file extension as first sign and file structure (by default first 1024 bytes) as second.
In most cases they must match (with some exceptions).
""",
    formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=60, width=120),
)
parser.add_argument('-p', '--path', dest='path', default='.', help='Path to file / dir')
parser.add_argument('-s', '--structure_size', dest='structure_size', type=int, default=1024, help='Size of structure for identify')
parser.add_argument('-v', '--verbose', dest='verbose', action='store_true', default=False, help='Verbose mode')
args = parser.parse_args()

scan_tree = []
scan_count = 0
if os.path.isdir(args.path):
    for (dir_path, dir_names, file_names) in os.walk(args.path):
        scan_tree.append([dir_path, file_names])
        scan_count += len(file_names)
else:
    dir_path, file_name = os.path.split(args.path)
    scan_tree.append([dir_path, [file_name]])
    scan_count = 1

print('Starting check for {} file(s) in {}'.format(scan_count, args.path))

results = {False: {}, True: {}}
check_count = 0
for dir_tree in scan_tree:
    for file_name in dir_tree[1]:
        file_path = dir_tree[0] + os.sep + file_name

        check_count += 1
        if args.verbose:
            progress = 100 * float(check_count) / scan_count
            print('progress: {:.1f}% | {} from {} | last file: {}'.format(progress, check_count, scan_count, file_path))
        else:
            print('.', end='', flush=True)

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in mimetypes.types_map:
            extension_mimetype = mimetypes.types_map[file_extension]
        else:
            continue
        # magic_mimetype = magic.from_file(file_path, mime=True)
        # magic.from_file doesn't supports unicode file names in Windows
        # so magic.from_buffer is more universal way
        try:
            file_size = os.path.getsize(file_path)
            file = open(file_path, 'rb')
            structure_size = min(args.structure_size, file_size)
            magic_mimetype = magic.from_buffer(file.read(structure_size), mime=True)
            file.close()
        except BaseException as e:
            print(e)
            break

        result_set = (file_extension, extension_mimetype, magic_mimetype)
        result = extension_mimetype == magic_mimetype
        if result is False and args.verbose:
            print('extension: {} != magic: {} for {}'.format(extension_mimetype, magic_mimetype, file_path))
        if result_set in results[result]:
            results[result][result_set] += 1
        else:
            results[result][result_set] = 1

print()
for result, result_name in {True: 'Success', False: 'Fail'}.items():
    print(result_name)
    for result_set, count in results[result].items():
        print('{} | {} | {} | {}'.format(result_set[0], result_set[1], result_set[2], count))
    print()
