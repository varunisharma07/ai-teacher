"""
Visual generator - turns a scene's visual_type + visual_description
(from /plan-lesson) into an actual image file.
----------------------------------------------------------------------
This is what satisfies the "subject-aware visual explanation"
requirement - a talking avatar alone isn't enough, so this module
renders the diagram/equation/code/slide that should appear alongside it.

Everything here runs locally with open-source libraries (matplotlib,
networkx, pygments, Pillow) - no new API key, no extra signup, and no
cost, matching the same approach as the RAG system.

HOW IT WORKS, high level:
- For diagrams: we first ask Gemini for a small structured list of
  steps/concepts and how they connect (nodes + edges), then draw that
  as a flowchart using networkx + matplotlib.
- For equations: we ask Gemini for the key equation in a simple
  math format, then render it with matplotlib (no LaTeX install needed).
- For code: we ask Gemini for a short illustrative code snippet, then
  syntax-highlight it into an image with pygments.
- For anything else (image/text_slide, or as a fallback): we render a
  clean text card with Pillow.
"""

import os
import json
import matplotlib
matplotlib.use("Agg")  # renders to a file, doesn't need a display
import matplotlib.pyplot as plt
import networkx as nx
from pygments import highlight
from pygments.lexers import guess_lexer, TextLexer
from pygments.formatters import ImageFormatter
from PIL import Image, ImageDraw, ImageFont

from google import genai
from google.genai import types

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_client = None

if os.getenv("GEMINI_API_KEY"):
    _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"


def _ask_gemini_json(prompt: str) -> dict:
    """Same pattern as main.py's helper - asks Gemini for JSON and
    handles the common failure modes clearly instead of crashing."""
    response = _client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.5),
    )
    if not response.candidates or response.candidates[0].content is None:
        raise RuntimeError("Gemini returned no usable content for this visual.")
    return json.loads(response.text)


def _ask_gemini_text(prompt: str) -> str:
    response = _client.models.generate_content(model=MODEL_NAME, contents=prompt)
    if not response.candidates or response.candidates[0].content is None:
        raise RuntimeError("Gemini returned no usable content for this visual.")
    return response.text.strip()


# ---------------------------------------------------------------------
# DIAGRAM: ask Gemini for a small step-by-step structure, then draw it
# as a top-to-bottom flowchart.
# ---------------------------------------------------------------------
def generate_diagram(description: str, output_path: str) -> str:
    prompt = f"""
Based on this description, create a simple flowchart structure with
3 to 6 short steps/concepts and how they connect.

Description: {description}

Respond ONLY with JSON in exactly this shape:
{{
  "nodes": ["Step 1 label", "Step 2 label", "..."],
  "edges": [["Step 1 label", "Step 2 label"], ["Step 2 label", "Step 3 label"]]
}}
Keep each label short (2-4 words).
"""
    structure = _ask_gemini_json(prompt)

    G = nx.DiGraph()
    G.add_nodes_from(structure["nodes"])
    G.add_edges_from(structure["edges"])

    # Arrange top-to-bottom by flow order instead of a random layout,
    # so it actually reads like a flowchart.
    try:
        layers = list(nx.topological_generations(G))
    except nx.NetworkXError:
        # Falls back to a simple single-row layout if the structure
        # has a cycle (shouldn't normally happen, but better safe).
        layers = [list(G.nodes)]

    pos = {}
    for layer_index, layer_nodes in enumerate(layers):
        for node_index, node in enumerate(layer_nodes):
            x = node_index - (len(layer_nodes) - 1) / 2
            y = -layer_index
            pos[node] = (x, y)

    fig, ax = plt.subplots(figsize=(7, 2 * max(len(layers), 1) + 1))
    nx.draw(
        G, pos, with_labels=True, node_color="#AED6F1", node_size=4500,
        font_size=10, font_weight="bold", arrows=True, ax=ax,
        edge_color="gray", arrowsize=20,
    )
    plt.margins(0.2)
    plt.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close()
    return output_path


# ---------------------------------------------------------------------
# EQUATION: ask Gemini for the key equation, render with matplotlib's
# built-in math rendering (mathtext) - no LaTeX installation needed.
# ---------------------------------------------------------------------
def generate_equation(description: str, output_path: str) -> str:
    prompt = f"""
Based on this description, give me the single most important equation,
written using simple math notation matplotlib's mathtext can render
(basic LaTeX-like syntax: use ^ for superscript, _ for subscript,
\\frac{{}}{{}} for fractions, standard operators). No explanation, just
the equation itself, without dollar signs.

Description: {description}
"""
    equation_text = _ask_gemini_text(prompt)

    fig = plt.figure(figsize=(7, 2))
    fig.text(0.5, 0.5, f"${equation_text}$", fontsize=26, ha="center", va="center")
    plt.axis("off")
    plt.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close()
    return output_path


# ---------------------------------------------------------------------
# CODE: ask Gemini for a short illustrative snippet, syntax-highlight
# it into an image with pygments.
# ---------------------------------------------------------------------
def generate_code_visual(description: str, output_path: str) -> str:
    prompt = f"""
Based on this description, write a short (5-12 line) illustrative code
snippet. Respond with ONLY the code itself, no explanation, no markdown
code fences.

Description: {description}
"""
    code_text = _ask_gemini_text(prompt)
    # Strip markdown fences if Gemini added them anyway
    code_text = code_text.strip("`").replace("python\n", "", 1) if code_text.startswith("```") else code_text

    try:
        lexer = guess_lexer(code_text)
    except Exception:
        lexer = TextLexer()

    formatter = ImageFormatter(font_size=20, line_numbers=True, style="monokai")
    image_bytes = highlight(code_text, lexer, formatter)
    with open(output_path, "wb") as f:
        f.write(image_bytes)
    return output_path


# ---------------------------------------------------------------------
# TEXT SLIDE: a clean text card, used for "text_slide"/"image" types
# or as a fallback if something above fails.
# ---------------------------------------------------------------------
def generate_text_slide(description: str, output_path: str, title: str = "") -> str:
    width, height = 1000, 560
    img = Image.new("RGB", (width, height), color="#1B2A4A")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 40)
        body_font = ImageFont.truetype("DejaVuSans.ttf", 28)
    except Exception:
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    y = 60
    if title:
        draw.text((60, y), title, font=title_font, fill="#FFFFFF")
        y += 80

    # Simple word-wrap so long descriptions don't run off the image
    words = description.split()
    line = ""
    max_chars_per_line = 55
    for word in words:
        test_line = f"{line} {word}".strip()
        if len(test_line) > max_chars_per_line:
            draw.text((60, y), line, font=body_font, fill="#E8ECF4")
            y += 42
            line = word
        else:
            line = test_line
    if line:
        draw.text((60, y), line, font=body_font, fill="#E8ECF4")

    img.save(output_path)
    return output_path


# ---------------------------------------------------------------------
# DISPATCHER: picks the right generator based on visual_type from
# /plan-lesson's scene JSON.
# ---------------------------------------------------------------------
def generate_visual(visual_type: str, description: str, output_path: str, topic: str = "") -> str:
    try:
        if visual_type == "diagram":
            return generate_diagram(description, output_path)
        elif visual_type == "equation":
            return generate_equation(description, output_path)
        elif visual_type == "code":
            return generate_code_visual(description, output_path)
        else:  # "image", "text_slide", or anything unrecognized
            return generate_text_slide(description, output_path, title=topic)
    except Exception as e:
        # If the specific renderer fails for any reason (Gemini hiccup,
        # bad structure, etc.), fall back to a plain text slide rather
        # than breaking the whole lesson generation.
        fallback_note = f"{description}\n\n(Note: could not render {visual_type} - {type(e).__name__})"
        return generate_text_slide(fallback_note, output_path, title=topic)
