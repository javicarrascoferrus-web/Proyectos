import os, re, base64, imaplib
from email import message_from_bytes
from email.header import decode_header
from flask import Flask, request

IMAP_HOST = os.getenv("IMAP_HOST", "imap.ionos.es")
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASS = os.getenv("IMAP_PASS", "")
MAX_POSTS = 10
EXCERPT = 250

app = Flask(__name__)

def dh(s):
    """Decode header"""
    if not s: return ""
    out = []
    for t, enc in decode_header(s):
        out.append(t.decode(enc or "utf-8", "replace") if isinstance(t, bytes) else t)
    return "".join(out)

def connect():
    M = imaplib.IMAP4_SSL(IMAP_HOST, 993)
    M.login(IMAP_USER, IMAP_PASS)
    M.select("INBOX")
    return M

def first_text_html_and_image(msg):
    html = text = None
    image = None

    for part in msg.walk():
        ctype = (part.get_content_type() or "").lower()
        disp = (part.get("Content-Disposition") or "").lower()
        if "attachment" in disp and not ctype.startswith("image/"):
            continue

        payload = part.get_payload(decode=True) or b""
        charset = part.get_content_charset() or "utf-8"

        if ctype == "text/html" and html is None:
            html = payload.decode(charset, "replace")
        elif ctype == "text/plain" and text is None:
            text = payload.decode(charset, "replace")
        elif ctype.startswith("image/") and image is None and payload:
            b64 = base64.b64encode(payload).decode("ascii")
            image = f"data:{ctype};base64,{b64}"

    return html, text, image

def excerpt_from_html(html, n=EXCERPT):
    txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()
    return (txt[:n] + "…") if len(txt) > n else txt

@app.route("/")
def index():
    uid = request.args.get("id")  
    M = connect()

    # buscar UIDs
    _, data = M.uid("search", None, "ALL")
    uids = data[0].split()[::-1] 

    # si es detalle, solo 1 UID
    if uid:
        uids = [uid.encode("ascii")]
    else:
        uids = uids[:MAX_POSTS]

    html_out = ["<h1>Blog de correos</h1>"]

    for u in uids:
        _, msgdata = M.uid("fetch", u, "(RFC822)")
        raw = msgdata[0][1]
        msg = message_from_bytes(raw)

        subject = dh(msg.get("Subject")) or "(Sin asunto)"
        sender = dh(msg.get("From")) or "(Desconocido)"
        uid_str = u.decode("ascii")

        html, text, image = first_text_html_and_image(msg)
        body = html or ("<pre>" + (text or "Sin contenido") + "</pre>")

        if not uid:  # portada: excerpt
            body = "<p>" + excerpt_from_html(body) + "</p>"

        html_out.append(f"<hr><h2><a href='/?id={uid_str}'>{subject}</a></h2>")
        html_out.append(f"<small>{sender}</small><br><br>")
        if image:
            html_out.append
        html_out.append(body)

        if uid:  
            break

    M.logout()
    return "".join(html_out)

if __name__ == "__main__":
    app.run(debug=True)
