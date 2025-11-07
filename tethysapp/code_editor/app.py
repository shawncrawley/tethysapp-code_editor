from tethys_sdk.components import ComponentBase
from django.views.decorators.clickjacking import xframe_options_sameorigin
from tethys_apps.base.page_handler import global_page_controller
from pathlib import Path
from reactpy import event

SUFFIX_TO_LANGUAGE = {
    '.py': 'python',
    '.html': 'html',
    '.js': 'javascript',
    '.css': 'css',
    '.gitkeep': None,
    '.gitignore': None,
    '': 'text'
}

TEST_APP_ROOT = r'C:\Users\Shawn.Crawley\Code\foss_dev\tethys_apps\tethysapp-delete_after_this'

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

@App.page(layout=None)
def test_bs_tabs(lib):
    key, set_key = lib.hooks.use_state('home')
    return lib.bs.Tabs(
        id="controlled-tab-example",
        activeKey=key,
        transition=False,
        onSelect=lambda k: print(k),
        className="mb-3",
    )(
        lib.bs.Tab(eventKey="home", title="Home")(
            "Tab content for Home"
        ),
        lib.bs.Tab(eventKey="profile", title="Profile")(
            "Tab content for Profile"
        ),
        lib.bs.Tab(eventKey="contact", title="Contact")(
            "Tab content for Contact"
        ),
    )

@App.page
def test_chakra_tabs(lib):
    tab_index, set_tab_index = lib.hooks.use_state(0)
    return lib.chakra.Tabs(index=tab_index, onChange=lambda i: set_tab_index(i))(
      lib.chakra.TabList(
        lib.chakra.Tab("One"),
        lib.chakra.Tab("Two"),
        lib.chakra.Tab("Three"),
      ),

      lib.chakra.TabPanels(
        lib.chakra.TabPanel(
          lib.html.p("one!")
        ),
        lib.chakra.TabPanel(
          lib.html.p("two!")
        ),
        lib.chakra.TabPanel(
          lib.html.p("three!")
        ),
      )
    )

@App.page
def home(lib):
    lib.register("react-icons", "icon", treat_as_path="all")
    lib.register('@monaco-editor/react', 'me', default_export="Editor")
    lib.register("react-folder-tree", "tree", styles=["https://esm.sh/react-folder-tree/dist/style.css"], default_export="FolderTree")
    lib.register("react-grid-layout", "grid", default_export="GridLayout")
    code_root_path = Path(TEST_APP_ROOT)
    tree_data = lib.hooks.use_memo(lambda: directory_to_dict(code_root_path))
    open_code_map, set_open_code_map = lib.hooks.use_state({})
    show_toast, set_show_toast = lib.hooks.use_state(False)
    open_files, set_open_files = lib.hooks.use_state([])
    active_file, set_active_file = lib.hooks.use_state(None)
    active_tab_index, set_active_tab_index = lib.hooks.use_state(0)

    def save_code():
        set_show_toast(True)
        active_file.write_text(open_code_map[str(active_file.resolve())])
        lib.utils.background_execute(lambda: set_show_toast(False), delay_seconds=2)

    def handle_file_tree_click(e):
        if e.nodeData.type == "directory": return
        if not any(e.nodeData.name.endswith(x) for x in SUFFIX_TO_LANGUAGE.keys()): return
        file_path = node_path_to_actual_path(code_root_path, tree_data, e.nodeData.path)
        set_active_file(file_path)
        if file_path in open_files:
            new_active_tab_index = open_files.index(file_path)
        else:
            new_open_files = open_files + [file_path]
            set_open_files(new_open_files)
            new_active_tab_index = len(new_open_files) - 1
        set_active_tab_index(new_active_tab_index)
    
    def handle_close_file(f):
        close_index = open_files.index(f)
        new_open_files = [i for i in open_files if i.resolve() != f.resolve()]
        set_open_files(new_open_files)
        if close_index == active_tab_index:
            set_active_tab_index(0)

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
                lib.tree.FolderTree(data=tree_data, showCheckbox=False, onNameClick=handle_file_tree_click),
            ),
            lib.bs.Col(
                lib.chakra.Tabs(
                    variant='enclosed-colored',
                    index=active_tab_index, 
                    onChange=lambda i: set_active_tab_index(i)
                )(
                    lib.chakra.TabList(
                        *[
                            lib.chakra.Tab(
                                f.name,
                                lib.html.span(style=lib.Style(width="3px")),
                                lib.html.span(
                                    on_click=(lambda _f: event(lambda _: handle_close_file(_f), stop_propagation=True, prevent_default=True))(f)
                                )(lib.icon.bs.BsXCircleFill())
                            ) for f in open_files
                        ]
                    ),
                    lib.chakra.TabPanels(
                        *[
                            lib.chakra.TabPanel(
                                lib.me.Editor(
                                    height="calc(100vh - 100px)",
                                    language=SUFFIX_TO_LANGUAGE[f.suffix],
                                    value=open_code_map[str(f.resolve())] if str(f.resolve()) in open_code_map else f.read_text(),
                                    onChange=(lambda _f: lambda v, _: set_open_code_map(open_code_map | {str(f.resolve()): v}))(f),
                                )
                            ) for f in open_files
                        ]
                    )
                )
            )
        )
    )
