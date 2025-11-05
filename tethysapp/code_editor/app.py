from tethys_sdk.components import ComponentBase


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
    code_root_path = Path("/home/cscott/foss4g/tethysapp-standard_app")
    user = lib.hooks.use_user()
    code_language, set_code_language = lib.hooks.use_state("python")
    tree_data = lib.hooks.use_memo(lambda: directory_to_dict(code_root_path))
    default_code_path = lib.hooks.use_resources().path / "default_code.py"
    default_code = lib.hooks.use_memo(lambda: default_code_path.read_text(), [])
    user_code, set_user_code = lib.hooks.use_state(None)
    uuid, set_uuid = lib.hooks.use_state(str(uuid4()))
    render_code = ""

    def handle_name_click(e):
        if e.nodeData.type == "directory": return
        if not any(e.nodeData.name.endswith(x) for x in ['.py', '.js', '.html', '.css']): return
        file_path = node_path_to_actual_path(code_root_path, tree_data, e.nodeData.path)
        set_user_code(file_path.read_text())
        if file_path.suffix == '.py':
            set_code_language("python")
        elif file_path.suffix == '.js':
            set_code_language("javascript")
        elif file_path.suffix == '.html':
            set_code_language("html")
        else:
            set_code_language("css")

    return lib.tethys.Display(
        lib.bs.Row(
            lib.bs.Button(
                on_click=lambda _: update_preview(),
            )(
                "Render"
            )
        ),
        lib.bs.Row(
            lib.bs.Col(
                lib.tree.FolderTree(data=tree_data, showCheckbox=False, onNameClick=handle_name_click),
            ),
            lib.bs.Col(
                lib.me.Editor(
                    height="70vh",
                    defaultLanguage=code_language,
                    value=render_code,
                    onChange=lambda v, _: set_user_code(v),
                ),
            ),
        )
    )

