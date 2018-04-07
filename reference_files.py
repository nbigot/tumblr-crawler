# -*- coding: utf-8 -*-

import pickle
import argparse
import os
import logging
import queue
import jinja2


def get_logger():
    logging.basicConfig(filename='reference_files.log',
                        format='%(asctime)s: %(message)s',
                        level=logging.DEBUG)
    logger = logging.getLogger()
    return logger


def render_html(directory, filenames):
    if not filenames:
        return False
    t = jinja2.Template("""
    <html>
    <body>
    <style>
    img {
        max-width: 100%;
        height: auto;
    }
    </style>
    <h1>Directory {{ directory }}</h1>
    <ul>
    {% for filename in filenames %}
    {% if filename.endswith('.mp4') %}
        <li>
            <video controls>
                <source src="{{filename}}" type="video/mp4">
            </video>
        </li>
    {% else %}
        <li><img src="{{filename}}" alt=""></li>
    {% endif %}
    {% endfor %}
    </ul>
    </body>
    </html>
    """)
    html = t.render(directory=directory, filenames=filenames)
    html_output_filename = os.path.join(directory, 'index.html')
    with open(html_output_filename, 'w') as f:
        f.write(html)
    return True


def build_html(verbose, directory, recursive):
    logger = get_logger()

    if verbose:
        logger.info('start build html')

    if not os.path.exists(directory):
        logger.error('directory not found %s', directory)
        return False

    q = queue.Queue()
    q.put(directory)
    dirs = dict()

    while not q.empty():
        cursor_dir = q.get()
        if cursor_dir not in dirs:
            dirs[cursor_dir] = {'files': set()}

        for (dir_path, dir_names, file_names) in os.walk(cursor_dir):
            if dir_path not in dirs:
                dirs[dir_path] = {'files': set()}

            for dir_name in dir_names:
                sub_dir = os.path.join(dir_path, dir_name)
                if verbose:
                    logger.debug('found dir %s', sub_dir)
                if recursive:
                    q.put(sub_dir)

            filter_files = {f for f in file_names
                            if (f.endswith('.gif') or
                                f.endswith('.jpg') or
                                f.endswith('.jpeg') or
                                f.endswith('.png') or
                                f.endswith('.mp4'))}
            if filter_files:
                dirs[dir_path]['files'] = filter_files.union(dirs[dir_path]['files'])

    for directory in dirs:
        render_html(directory, dirs[directory]['files'])

    return True


def reference_files(verbose, pickle_filepath, directory, filenames):
    logger = get_logger()

    if verbose:
        logger.info('reference files in {}'.format(directory))

    if os.path.exists(pickle_filepath):
        with open(pickle_filepath, 'rb') as fp:
            data = pickle.load(fp)
    else:
        data = {'dirs': dict()}

    if directory not in data['dirs']:
        data['dirs'][directory] = {'files': set()}

    previous_filename_set = data['dirs'][directory]['files']
    data['dirs'][directory]['files'] = previous_filename_set.union(filenames)

    with open(pickle_filepath, 'wb') as fp:
        pickle.dump(data, fp)


def reference_directories(verbose, pickle_filepath, directory, recursive):
    logger = get_logger()

    if verbose:
        logger.info('start referencing files')

    if not os.path.exists(directory):
        logger.error('directory not found %s', directory)
        return False

    q = queue.Queue()
    q.put(directory)
    dirs_found = set()

    while not q.empty():
        cursor_dir = q.get()
        if cursor_dir not in dirs_found:
            dirs_found.add(cursor_dir)

        for (dir_path, dir_names, file_names) in os.walk(cursor_dir):
            if dir_path not in dirs_found:
                dirs_found.add(dir_path)

            for dir_name in dir_names:
                sub_dir = os.path.join(dir_path, dir_name)
                if verbose:
                    logger.debug('found dir %s', sub_dir)
                if recursive:
                    q.put(sub_dir)

            filter_files = {f for f in file_names
                            if (f.endswith('.gif') or
                                f.endswith('.jpg') or
                                f.endswith('.jpeg') or
                                f.endswith('.png') or
                                f.endswith('.mp4'))}

            reference_files(verbose, pickle_filepath, dir_path, filter_files)

    return True


if __name__ == "__main__":
    sites = None

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", action="store_true", default=False, help="increase output verbosity")
    parser.add_argument("-html", "--html", action="store_true", default=False, help="pickle file path")
    parser.add_argument("-p", "--pickle", help="pickle file path")
    parser.add_argument("-d", "--directory", required=True, help="output root directory path")
    parser.add_argument("-r", "--recursive", action="store_true", default=False, help="parse directories recursively")
    args = parser.parse_args()

    if args.html:
        build_html(args.verbose, args.directory, args.recursive)
    else:
        reference_directories(args.verbose,
                              args.pickle,
                              args.directory,
                              args.recursive)
