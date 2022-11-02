from pathlib import Path


TEMPLATES_DIR = Path(__file__).parent.absolute()

ABOUT_STYLESHEET_FILE = TEMPLATES_DIR.joinpath("about_stylesheet.css")

ABOUT_TEMPLATE_FILE = TEMPLATES_DIR.joinpath("about_template.jinja_html")


DEBUG_LIST_OF_DICTS_CONTENT_TEMPLATE_FILE = TEMPLATES_DIR.joinpath("debug_list_of_dicts_content.jinja_html")
