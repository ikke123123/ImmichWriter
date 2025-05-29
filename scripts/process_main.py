import modules.scripts as scripts
import gradio as gr
import requests
import io

from typing_extensions import Protocol
from PIL import Image
from datetime import datetime
from modules.processing import Processed
from modules.shared import opts, OptionInfo
from modules import script_callbacks, scripts_postprocessing

immich_writer = "Immich Writer"

def log_text(text):
    print(f" [-] Immich Writer: {text}")

def on_ui_settings():
    section = ('immich', "Immich")
    opts.add_option(
        "immich_url",
        OptionInfo(
            "immich.app",
            "Immich Url:",
            gr.Textbox,
            {"interactive": True},
            section=section)
    )
    opts.add_option(
        "immich_api_key",
        OptionInfo(
            "abcd1234",
            "Immich API key:",
            gr.Textbox,
            {"interactive": True},
            section=section)
    )
    opts.add_option(
        "immich_send_default",
        OptionInfo(
            False,
            "Send image to Immich by default",
            gr.Checkbox,
            {"interactive": True},
            section=section)
    )

script_callbacks.on_ui_settings(on_ui_settings)

def save(im: Image.Image):
    file_decoration = f'{datetime.now()}'
    file_extension = opts.samples_format
    filename = f'{file_decoration}.{file_extension}'

    log_text(f"Sending image '{filename}' to Immich!")

    headers = {
        'Accept': 'application/json',
        'x-api-key': opts.immich_api_key
    }

    data = {
        'deviceAssetId': file_decoration,
        'deviceId': 'stable-diffussion:immich-writer-extension',
        'fileCreatedAt': datetime.now(),
        'fileModifiedAt': datetime.now(),
        'isFavorite': 'false',
    }

    item = io.BytesIO()
    im.save(item, file_extension)
    item.seek(0)
    buffered_reader = io.BufferedReader(item)

    files = {
        ('assetData', (filename, buffered_reader, 'application/octet-stream'))
    }

    response = requests.post(
        f'https://{opts.immich_url}/api/assets', headers=headers, data=data, files=files)

    log_text(f"statuscode={response.status_code} file='{filename}' response={response.json()}")

class PPImage(Protocol):
    image: Image.Image

class ImmichWriter(scripts.Script):
    def __init__(self) -> None:
        super().__init__()

    def __repr__(self):
        return f"{self.__class__.__name__})"

    def title(self):
        return immich_writer

    def show(self, _):
        return scripts.AlwaysVisible

    def ui(self, _):
        immich_send_default = opts.immich_send_default

        with gr.Accordion(immich_writer, open=False):
            with gr.Row():
                enabled = gr.Checkbox(
                    immich_send_default,
                    label="Enable Upload"
                )
        return [enabled]

    def postprocess(self, _, pp: Processed, enabled):
        if (enabled):
            for i in range(len(pp.images)):
                save(pp.images[i])

class ScriptPostprocessingImmichWriter(scripts_postprocessing.ScriptPostprocessing):
    name = immich_writer
    order = 99999999 # We want this value to be last in the UI

    def ui(self):
            immich_send_default = opts.immich_send_default

            with gr.Accordion(immich_writer, open=False):
                enabled = gr.Checkbox(
                    immich_send_default,
                    label="Enable Upload"
                )

            return { "immich_send_enabled" : enabled }

    def postprocess(self, images, immich_send_enabled):
        if (immich_send_enabled):
            for i in range(len(images)):
                save(images[i])

    def image_changed(self):
        pass
