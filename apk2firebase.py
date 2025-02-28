# Make sure apktool is added to path before you run this

import sys
import subprocess
import threading
import os
import re
import xml.etree.ElementTree as ElementTree
import shutil
import requests
import random
from argparse import ArgumentParser
import pyfiglet

def print_banner(output_file=None):
    banner = pyfiglet.figlet_format("apk2firebase")
    print_stdout(banner, output_file)
    print_stdout("     === Dig the Firebase credentials from APKs! ===", output_file)
    print_stdout("            === By Riley Kivimäki (kivirnz) ===", output_file)
    print_stdout(" ")
    print()


def print_stdout(message, output_file=None):
    print(message)
    if output_file:
        with open(output_file, 'a') as f:
            f.write(message + "\n")

def run_apktool(apk_file):
    proc = subprocess.Popen(['apktool', 'd', apk_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc

def mon_stdout(proc, dir_name, no_test, output_file=None):
    while True:
        output = proc.stdout.readline()
        if output == b'' and proc.poll() is not None:
            break
        if b'Decoding' in output and b'XMLs' in output:
            proc.stdout.readline()
            break

    proc.wait()
    load_xml(dir_name, no_test, output_file)
    cleanup(dir_name, output_file)

def load_xml(dir_name, no_test, output_file=None):
    xml_path = os.path.join(dir_name, 'res', 'values', 'strings.xml')
    if not os.path.isfile(xml_path):
        print()
        print_stdout("[+] strings.xml not found in the APK file. L, better luck next time bozo.", output_file)
        return

    tree = ElementTree.parse(xml_path)
    root = tree.getroot()

    db_url = None
    apikey = None
    projectid = None

    db_pattern = re.compile(r'.*database.*url.*', re.IGNORECASE)
    apikey_pattern = re.compile(r'.*api.*key.*', re.IGNORECASE)
    id_pattern = re.compile(r'.*project.*id.*', re.IGNORECASE)

    for string in root.findall('string'):
        name = string.get('name')
        value = string.text

        if db_pattern.match(name):
            db_url = value
        elif apikey_pattern.match(name):
            apikey = value if value and value.startswith("AIza") else None
        elif id_pattern.match(name):
            projectid = value

    if not apikey:
        for string in root.findall('string'):
            value = string.text
            if value and value.startswith("AIza"):
                apikey = value
                break

    if projectid is None and db_url is not None:
        projectid = db_url.split('.')[1]

    print_stdout(f"apiKey: {apikey or 'not found.'}", output_file)
    print_stdout(f"databaseURL: {db_url or 'not found.'}", output_file)
    print_stdout(f"projectId: {projectid or 'not found.'}", output_file)
    print_stdout(f"authDomain: {projectid}.firebaseapp.com" if projectid else "authDomain not found.", output_file)

    if not no_test:
        if db_url:
            test_db_connection(db_url, output_file)
        else:
            print()
            print_stdout("[+] Unable to test Firebase database connection due to not being able to find a database URL in the APK.", output_file)

def test_db_connection(db_url, output_file=None):
    url = f"{db_url}/.json"
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
        "Mozilla/5.0 (Linux; Android 10; SM-G970F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.120 Mobile Safari/537.36"
    ]
    headers = {"User-Agent": random.choice(user_agents)}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 401 and 'Permission denied' in response.text:
            print()
            print_stdout("[+] Permission denied. Unauthenticated users are denied by default. Try with https://github.com/0xbigshaq/firepwn-tool to see if you can create an account on the database.", output_file)
        elif 'has been deactivated' in response.text:
            print()
            print_stdout("[+] The Firebase database has been deactivated. This means that the developers have shut down the Firebase instance for this program.", output_file)
        elif response.text == "null":
            print()
            print_stdout("[+] Null response detected! This Firebase database may allow for unauthenticated users to read (and possibly write). Test this further with https://github.com/0xbigshaq/firepwn-tool.", output_file)
        else:
            print()
            print_stdout("[+] Random JSON detected! This could either mean that the database is returning information or that an error has possibly occurred. It's recommended to test this further with https://github.com/0xbigshaq/firepwn-tool.", output_file)
    except requests.RequestException as e:
        print_stdout(f"Failed to connect to Firebase database to test: {e}", output_file)

def cleanup(dir_name, output_file=None):
    if os.path.isdir(dir_name):
        try:
            shutil.rmtree(dir_name)
        except Exception as e:
            print_stdout(f"Can't remove directory {dir_name}: {e}", output_file)

def process_apk(apk_path, apk_name=None, no_test=False, output_file=None):
    print_stdout(f"{os.path.basename(apk_name if apk_name else apk_path)}:", output_file)
    dir_name = os.path.splitext(os.path.basename(apk_path))[0]
    proc = run_apktool(apk_path)

    thread = threading.Thread(target=mon_stdout, args=(proc, dir_name, no_test, output_file))
    thread.start()
    thread.join()
    print_stdout("", output_file)

def scan_directory(dir_path, no_test=False, output_file=None):
    for file in os.listdir(dir_path):
        if file.endswith('.apk'):
            file_path = os.path.join(dir_path, file)
            process_apk(file_path, no_test=no_test, output_file=output_file)
        elif file.endswith('.xapk'):
            print_stdout("[+] XAPK extraction is not supported due to the developer (me) being a fucking sped. Please just unzip the main application APK out of the XAPK yourself and rerun it. Thanks.", output_file)

def main():
    parser = ArgumentParser(description="Extract Firebase credentials from APKs")
    parser.add_argument("apk", nargs="?", help="Path to a single APK file")
    parser.add_argument("-d", "--directory", help="Path to directory containing APK files")
    parser.add_argument("--no-test", action="store_true", help="Skip Firebase connection tests")
    parser.add_argument("-o", "--output", help="Path to output file")
    args = parser.parse_args()

    print_banner(args.output)

    if args.directory:
        scan_directory(args.directory, no_test=args.no_test, output_file=args.output)
    elif args.apk:
        if args.apk.endswith('.apk'):
            process_apk(args.apk, no_test=args.no_test, output_file=args.output)
        elif args.apk.endswith('.xapk'):
            print_stdout("[+] XAPK extraction is not supported due to the developer (me) being a fucking sped. Please just unzip the main application APK out of the XAPK yourself and rerun it. Thanks.", args.output)
    else:
        print_stdout("Usage: python apk2firebase.py APP_NAME.apk or -d DIRECTORY_NAME", args.output)

if __name__ == '__main__':
    main()
