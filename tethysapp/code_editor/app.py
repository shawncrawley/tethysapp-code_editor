from tethys_sdk.components import ComponentBase
from django.views.decorators.clickjacking import xframe_options_sameorigin
from tethys_apps.base.page_handler import global_page_controller
from pathlib import Path

SUFFIX_TO_LANGUAGE = {
    '.py': 'python',
    '.html': 'html',
    '.js': 'javascript',
    '.css': 'css'
}


class App(ComponentBase):
    """
    Tethys app class for Code Editor.
    """

    name = "Code Editor"
    description = "Edit the code for your app right in the browser."
    package = "code_editor"  # WARNING: Do not change this value
    index = "home"
    icon = f"{package}/images/icon.png"
    root_url = "code-editor"
    color = "#718093"
    tags = ""
    enable_feedback = False
    feedback_emails = []
    exit_url = "/apps/"
    default_layout = "NavHeader"
    nav_links = "auto"


@xframe_options_sameorigin
def handler(*args, **kwargs):
    return global_page_controller(*args, **kwargs)

def directory_to_dict(path):
    """
    Recursively walks a directory and creates a dictionary representation of the 
    tree structure.

    Args:
        path (Path): The path to the root directory.

    Returns:
        dict: A dictionary representation of the directory tree.
    """
    node = {
        "name": path.name,
        "type": "directory" if path.is_dir() else "file"
    }

    if node["type"] == "directory":
        node["children"] = []
        try:
            # Iterate over directory entries
            for entry in path.iterdir():
                if entry.suffix in ['.pyc', '.egg-info'] or entry.name in ["__pycache__", ".git"]:
                    continue
                # Recursively call the function for each entry
                node["children"].append(directory_to_dict(entry))
        except OSError:
            # Handle cases with permission errors or other access issues
            pass 
    
    return node

def node_path_to_actual_path(code_root_path, data_tree, node_path):
    iter_tree = data_tree
    fpath = code_root_path
    for index in node_path:
        iter_tree = iter_tree['children'][index]
        fpath /= iter_tree['name']

    return(fpath)

@App.page
def home(lib):
    lib.register('@monaco-editor/react', 'me', default_export="Editor")
    lib.register("react-folder-tree", "tree", styles=["https://esm.sh/react-folder-tree/dist/style.css"], default_export="FolderTree")
    lib.register("react-grid-layout", "grid", default_export="GridLayout")
    code_root_path = Path("/home/cscott/foss4g/tethysapp-standard_app")
    user = lib.hooks.use_user()
    code_language, set_code_language = lib.hooks.use_state("text")
    code_path, set_code_path = lib.hooks.use_state(None)
    tree_data = lib.hooks.use_memo(lambda: directory_to_dict(code_root_path))
    editor_code, set_editor_code = lib.hooks.use_state(None)
    show_toast, set_show_toast = lib.hooks.use_state(False)

    def save_code():
        set_show_toast(True)
        code_path.write_text(editor_code)
        lib.utils.background_execute(lambda: set_show_toast(False), delay_seconds=2)

    def handle_name_click(e):
        if e.nodeData.type == "directory": return
        if not any(e.nodeData.name.endswith(x) for x in SUFFIX_TO_LANGUAGE.keys()): return
        file_path = node_path_to_actual_path(code_root_path, tree_data, e.nodeData.path)
        set_code_path(file_path)
        set_editor_code(file_path.read_text())
        set_code_language(SUFFIX_TO_LANGUAGE[file_path.suffix])

    return lib.tethys.Display(
        lib.html.div(style=lib.Style(position="absolute", right=0, left=0, top="50px"))(
            lib.bs.Toast(show=show_toast)(
                lib.bs.ToastBody("Save successful!"),
            )
        ),
        lib.bs.Row(
            lib.bs.Button(
                on_click=lambda _: save_code(),
            )("Save")
        ),
        lib.bs.Row(
            lib.bs.Col(xs=3, sm=3, md=3, lg=3, xl=3, xxl=3)(
                lib.tree.FolderTree(data=tree_data, showCheckbox=False, onNameClick=handle_name_click),
            ),
            lib.bs.Col(
                lib.me.Editor(
                    height="70vh",
                    language=code_language,
                    value=editor_code or "",
                    onChange=lambda v, _: set_editor_code(v),
                ),
            ),
        )
    )

