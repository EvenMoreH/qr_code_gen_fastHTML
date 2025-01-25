from fasthtml.common import * # type: ignore
import qrcode # type: ignore
import time
from datetime import datetime
import os
from starlette.responses import FileResponse
from mimetypes import guess_type

# for Docker
app, rt = fast_app(static_path="static") # type: ignore

# for local
# app, rt = fast_app(static_path="app/static") # type: ignore

# handling temp files directory
temp_dir = Path("app/temp")
temp_dir.mkdir(parents=True, exist_ok=True)

# generator logic
def generate_qr_code(url):
    # Ensure the target dir exists
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

# removing temp files
def remove_old_files(folder, seconds):
    # Calculate the threshold time (in seconds)
    now = time.time()
    age_threshold = now - seconds  # 2 days = 2 * 86400 seconds

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)

        # Check if it's a file
        if os.path.isfile(file_path):
            # Get the file's last modified time
            file_mtime = os.path.getmtime(file_path)

            # Check if the file is older than the threshold
            if file_mtime < age_threshold:
                log_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"LOG: {log_time} - Removing old file: {file_path}")
                os.remove(file_path)  # Delete the file

# js script for download button
download_script = """
        function download(filename, extension) {
        const url = `/download/${filename}/${extension}`;
        window.location.href = url;
    }
    """

@rt("/")
def homepage():
    time_to_remove = 1200 # Removing generated .png after 20 minutes
    remove_old_files(temp_dir, time_to_remove)  # Removes files older than [in seconds]
    return Html(
        Head(
            Title("QR Code Gen"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Script(src="https://unpkg.com/htmx.org"),
            Link(rel="stylesheet", href="css/tailwind.css"),
            Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
            Link(rel="icon", href="images/favicon.png", type="image/png"),
        ),
        Body(
            Div(
                Titled("QR Code Generator",
                cls="text-3xl md:text-5xl font-bold mb-8 md:p-2 p-0.5 text-center xl:text-center"),
            ),
            Div(
                Form(
                    Div(
                        Input(
                            id="url",
                            type="text",
                            name="url",
                            required=True,
                            placeholder="Your URL",
                            cls="max-w-[80vw] w-80 sm:w-3/5 md:w-2/4 lg:w-1/3 bg-dark-theme-lightgray text-gray-100 pl-2 min-h-9 rounded-md shadow-md shadow-black",
                        ),
                        cls="",
                    ),
                    Div(cls="m-6"),
                    Div(
                        Button(
                            "Generate QR Code",
                            type="submit",
                            cls="btn",
                        ),
                        cls="",
                    ),
                    action="/qr",
                    method="post",
                    cls="container mx-auto"
                ),
                cls="container mx-auto items-center text-center pb-[20vh]"
            ),
            cls="bg-dark-theme-gray text-gray-100 h-full place-content-center text-lg"
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
                Link(rel="stylesheet", href="css/tailwind.css"),
                Link(rel="icon", href="images/favicon.ico", type="image/x-icon"),
                Link(rel="icon", href="images/favicon.png", type="image/png"),
            ),
            Body(
                Titled("QR Code Ready", cls="text-3xl md:text-5xl font-bold mb-8 md:p-2 p-0.5 text-center xl:text-center"),
                Div(
                    H3("Preview", cls="text-xl md:text-2xl font-bold pb-2 text-center xl:text-center"),
                    Img(src=f"/download/{filename}/{extension}", alt="img",
                        style="max-width: clamp(230px, 70vw, 256px); height: auto; margin: auto;",
                        cls="pt-2 pb-2"
                    ),
                    A("Hover to see URL", href=f"{log_url}", title=f"{log_url}",
                        cls="hover:text-blue-200 transition-all duration-200 mx-auto mt-2 mb-2 font-bold"),
                    cls="text-center",
                ),
                Div(cls="p-2 md:p-6"),
                Div(
                    Button(
                        "Download QR Code",
                        onclick=f"download('{filename}', '{extension}')",
                        cls="btn",
                    ),
                    cls="text-center"
                ),
                Div(cls="p-3"),
                Div(
                    Form(
                        Button(
                            "Return",
                            type="submit",
                            cls="btn",
                        ),
                        action="/",
                        method="get",
                    ),
                    cls="text-center"
                ),
                cls="bg-dark-theme-gray text-gray-100 h-full place-content-center text-lg"
            )
        )


if __name__ == '__main__':
    # Important: Use host='0.0.0.0' to make the server accessible outside the container
    serve(host='0.0.0.0', port=5015) # type: ignore