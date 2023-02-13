#!/usr/bin/env python3

import os
import sys
import argparse
import json
import urwid 
from plainbox.impl.session.assistant import SessionAssistant
from plainbox.impl.highlevel import Explorer
from checkbox_ng.urwid_ui import ManifestBrowser

DEFAULT_PROMPT = "Does this machine have this piece of hardware?"

white_list = [
    "com.canonical.certification::has_wwan_module",
    "com.canonical.certification::has_ethernet_adapter",
    "com.canonical.certification::has_camera",
    "com.canonical.certification::has_usb_storage",
    "com.canonical.certification::has_tpm2_chip",
    "com.canonical.certification::has_wlan_adapter",
    "com.canonical.certification::has_bt_smart",
    "com.canonical.certification::has_camera",
    "com.canonical.certification::has_card_reader",
    "com.canonical.certification::has_dp",
    "com.canonical.certification::has_dvi",
    "com.canonical.certification::has_fingerprint_reader",
    "com.canonical.certification::has_hdmi",
    "com.canonical.certification::has_special_keys",
    "com.canonical.certification::has_thunderbolt3",
    "com.canonical.certification::has_touchpad",
    "com.canonical.certification::has_touchscreen",
    "com.canonical.certification::has_usbc_data",
    "com.canonical.certification::has_usbc_video",
    "com.canonical.certification::has_vga",
]


def save_manifest(manifest_answers, manifest_path):
    """
    Record the manifest on disk.
    """
    manifest_cache = dict()
    if os.path.isfile(manifest_path):
        with open(manifest_path, 'rt', encoding='UTF-8') as stream:
            manifest_cache = json.load(stream)
    
    manifest_cache.update(manifest_answers)
    print("Saving manifest to {}".format(manifest_path))
    with open(manifest_path, 'wt', encoding='UTF-8') as stream:
        json.dump(manifest_cache, stream, sort_keys=True, indent=2)


def parse_arguments():
    description = "This utility is for generate a checkbox manifest file"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-o",
        "--output_file",
        required=True,
        help="generate a checkbox manifest configuration"
    )
    return parser.parse_args(sys.argv[1:])
    

def main():
    args = parse_arguments()

    sa = SessionAssistant(
        "com.canonical:checkbox-cli",
        "0.99",
        "0.99",
        ["restartable"],
    )
    providers = sa.get_selected_providers()
    obj = Explorer(providers).get_object_tree()
    
    manifest_info = dict()

    def get_necessary_jobs(content):
        jobs = []
        if content.group == "manifest entry":
            print(content.name)
            if content._impl.id in white_list:

                prompt = content._impl.prompt()
                value_type = content._impl.value_type
                if prompt is None:
                    if value_type == "bool":
                        prompt = DEFAULT_PROMPT
                    elif value_type == "natural":
                        prompt = "Please enter the requested data:"

                if prompt not in manifest_info:
                    manifest_info[prompt] = []

                manifest = {
                    "id": content._impl.id,
                    "partial_id": content._impl.partial_id,
                    "name": content._impl.name,
                    "value_type": value_type,
                    "value": None
                }
                manifest_info[prompt].append(manifest)

        for child in content.children:
            jobs += get_necessary_jobs(child)

        return jobs
    
    get_necessary_jobs(obj)

    manifest_browser = ManifestBrowser("System Manifest:", manifest_info)
    footer_text = [
        ('Press ('), 
        ('start', 'T'), 
        (') to generate manifest file')
    ]
    default_footer = urwid.AttrWrap(urwid.Columns(
        [urwid.Padding(urwid.Text(footer_text), left=1),
         urwid.Text(manifest_browser.footer_shortcuts, 'right')]), 'foot')
    # Update Main frame
    manifest_browser.frame = urwid.Frame(
            urwid.AttrWrap(urwid.LineBox(manifest_browser.listbox), 'body'),
            header=urwid.AttrWrap(manifest_browser.header, 'head'),
            footer=default_footer)
    manifest_answers = manifest_browser.run()

    save_manifest(manifest_answers, args.output_file)


if __name__ == "__main__":
    main()
