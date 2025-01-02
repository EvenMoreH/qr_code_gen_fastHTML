from fasthtml.common import * # type: ignore
from fasthtml.common import (
    Button, Html, Head, Body, Div, Title, Titled, Link, Meta, Script, Input, Redirect
)
import qrcode # type: ignore
from datetime import datetime
import os
from starlette.responses import FileResponse
from mimetypes import guess_type

# for Docker
# app, rt = fast_app(static_path="static") # type: ignore

# for local
app, rt = fast_app(static_path="app/static") # type: ignore

def generate_qr_code(url):
    # Ensure the target dir exists (docker)
    # output_dir = "temp"

    # Ensure the target dir exists (local)
    output_dir = "app/temp"
    os.makedirs(output_dir, exist_ok=True)

    # Generate a timestamped filename
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
    sanitized_url = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_")
    global filename
    filename = f"qrcode_{sanitized_url[:24]}_{timestamp}.png"
    global file_path
    file_path = os.path.join(output_dir, filename)

    # Create the QR code
    qr = qrcode.QRCode(
        version=10,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save(file_path)

    filename = filename.rstrip(".png")

    global extension
    extension = "png"

download_script = """
        function download(filename, extension) {
        const url = `/download/${filename}/${extension}`;
        window.location.href = url;
    }
    """

@rt("/")
def homepage():
    return Html(
        Head(
            Title("QR Code Gen"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Script(src="https://unpkg.com/htmx.org"),
            Link(rel="stylesheet", href="styles.css"),
            Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
            Link(rel="icon", href="images/favicon.png", type="image/png"),
        ),
        Body(
            Div(
                Titled("QR Code Generator", cls="title"),
                cls="container",
            ),
            Form(
                Div(
                    Input(
                        id="url",
                        type="text",
                        name="url",
                        required=True,
                        placeholder="Your URL",
                        cls="input",
                    ),
                    cls="container",
                ),
                Div(
                    Button(
                        "Generate QR Code",
                        type="submit",
                    ),
                    cls="container",
                ),
                action="/qr",
                method="post",
            )
        )
    )


@rt("/qr")
def qr(url: str):
    generate_qr_code(url)
    global log_url
    log_url = url
    return Redirect (f"/code/{filename}/{extension}")

@rt("/download/{filename}/{extension}", methods=["GET"])
async def download(filename: str, extension: str):
    if not os.path.exists(file_path):
        return Response("File not found", status_code=404)

    # Guess MIME type
    mime_type, _ = guess_type(file_path)
    if not mime_type:
        mime_type = "application/octet-stream"  # fallback

    return FileResponse(
        file_path,
        media_type=mime_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}.{extension}"'}
    )

@rt("/code/{filename}/{extension}", methods=["GET"])
def code_ready(filename: str, extension: str):
        print(f"[LOG]: Converted URL: {log_url}")
        return Html(
            Head(
                # using base with only "/" to make the path absolute - works locally
                Base(href="/"),
                Meta(name="viewport", content="width=device-width, initial-scale=1"),
                Script(src="https://unpkg.com/htmx.org"),
                Script(download_script),
                Title("QR Code Gen"),
                Link(rel="stylesheet", href="styles.css"),
                Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
                Link(rel="icon", href="images/favicon.png", type="image/png"),
            ),
            Body(
                Titled("QR Code Ready"),
                Div(
                    H1("Preview", style="min-width: 220px", cls="title"),
                    Img(src=f"/download/{filename}/{extension}", alt="img", style="max-width: clamp(180px, 70vw, 256px); height: auto; margin: auto;"),
                    A(f"{log_url}", href=f"{log_url}"),
                    cls="container",
                ),
                Div(
                     Button(
                          "Download QR Code",
                          onclick=f"download('{filename}', '{extension}')",
                          cls="container",
                     ),
                ),
            ),
        )


if __name__ == '__main__':
    # Important: Use host='0.0.0.0' to make the server accessible outside the container
    serve(host='0.0.0.0', port=5001) # type: ignore