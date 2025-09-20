import copy
import curses
import os.path
import sys

from kanban_board import KanbanBoard

#Accositate the priority with numbers
LOW_PRIORITY = 1
MEDIUM_PRIORITY = 1
HIGH_PRIORITY = 3

#Set the folder to where the save files will be stored
documents_path = os.path.join(os.path.expanduser("~"), "Documents")
folder_name = "TermiKanban Boards"
folder_path = os.path.join(documents_path, folder_name)

#The variable for the theme
current_theme = 'default'

def init_colors():
    """
    Initializes curses color pairs
    :return: None
    """
    curses.start_color()
    curses.use_default_colors()

    if current_theme == "default":
        curses.init_pair(LOW_PRIORITY, curses.COLOR_WHITE, -1)
        curses.init_pair(MEDIUM_PRIORITY, curses.COLOR_YELLOW, -1)
        curses.init_pair(HIGH_PRIORITY, curses.COLOR_RED, -1)
    elif current_theme == 'dark_blue':
        curses.init_pair(LOW_PRIORITY, curses.COLOR_CYAN, -1)
        curses.init_pair(MEDIUM_PRIORITY, curses.COLOR_MAGENTA, -1)
        curses.init_pair(HIGH_PRIORITY, curses.COLOR_RED, -1)

def draw_board(stdscr, board, selected_col=0, selected_card=0):
    """
    Renders the current state of the board

    :param stdscr: A curses window object used to draw on the terminal screen.
    :type stdscr: _curses.window
    :param board: The data structure containing the columns and cards to render.
    :type board: Board
    :param selected_col: The index of the currently selected column.
    :type selected_col: int
    :param selected_card: The index of the currently selected card within the selected column.
    :type selected_card: int
    :return: None
    """
    curses.curs_set(0)
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    col_width = width // len(board.columns) if board.columns else width

    #Draw each column and its cards
    for i, column in enumerate(board.columns):
        x_start = i * col_width
        stdscr.addstr(0, x_start, column.name, curses.A_BOLD)
        y_offset = 2
        #Sort the cards by priority (high to low)
        sorted_cards = sorted(column.cards, key=lambda c: c.priority, reverse=True)
        for j, card in enumerate(sorted_cards):
            color = curses.color_pair(card.priority)
            #Highlight selected card
            attr = color | (curses.A_REVERSE if i == selected_col and j == selected_card else 0)
            if y_offset < height -1:
                stdscr.addstr(y_offset, x_start, f"- {card.title}", attr)
                y_offset += 1
                if y_offset < height:
                    stdscr.addstr(y_offset, x_start + 2, f"{card.description}", attr)
                    y_offset += 1
    stdscr.refresh()

def file_picker(stdscr, path=str(folder_path)):
    """
    Display a file picker to choose from .kanban files

    If no .kanban files are found says "found no .kanban files"

    User can select using Enter and exit using ESC

    :param stdscr: A curses window object representing the standard screen used
                   for displaying content within the terminal.
    :type stdscr: _curses.window
    :param path: Path to the directory from which to list and select `.kanban`
                 files. Defaults to the folder_path.
    :type path: str
    :return: Absolute path to the selected `.kanban` file, or None if no file was
             selected or the picker was canceled.
    :rtype: Optional[str]
    """
    files = [f for f in os.listdir(path) if f.endswith(".kanban")] #.kanban is the format the save files are stored in
    if not files:
        stdscr.addstr(15, 0, "No .kanban files found")
        stdscr.getch()
        return None

    idx = 0
    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select a file to open:")
        for i , fname in enumerate(files):
            if i == idx:
                stdscr.addstr(i + 2, 2, fname, curses.A_REVERSE)
            else:
                stdscr.addstr(i + 2, 2, fname)

        key = stdscr.getch()
        if key in (curses.KEY_UP, ord('k')) and idx > 0:
            idx -= 1
        elif key in (curses.KEY_DOWN, ord('j')) and idx < len(files) -1:
            idx += 1
        elif key in (curses.KEY_ENTER, 10, 13):
            return os.path.join(path, files[idx])
        elif key == 27:  # ESC to cancel
            return None

def get_input(stdscr, y, x, prompt, max_length):
    """
    Gets input from the user using curses

    :param stdscr: The curses window object where input and prompt will be displayed.
    :type stdscr: curses.window
    :param y: The Y-coordinate (row) within the curses window where the input prompt is shown.
    :type y: int
    :param x: The X-coordinate (column) within the curses window where the input prompt is shown.
    :type x: int
    :param prompt: The text prompt displayed before user input.
    :type prompt: str
    :param max_length: The maximum allowable length of the input string.
    :type max_length: int
    :return: The string input entered by the user.
    :rtype: str
    """
    curses.curs_set(1)  # Show cursor
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    inp = ""

    while True:
        key = stdscr.getch(y, x + len(prompt) + len(inp))
        if key in (curses.KEY_ENTER, 10, 13):  # Enter key
            break
        elif key in (curses.KEY_BACKSPACE, 127, 8):  # Backspace
            if len(inp) > 0:
                inp = inp[:-1]
                stdscr.addstr(y, x + len(prompt), inp + " " * (max_length - len(inp)))
                stdscr.move(y, x + len(prompt) + len(inp))
        elif 32 <= key <= 126 and len(inp) < max_length:  # Printable characters
            inp += chr(key)
            stdscr.addstr(y, x + len(prompt), inp)
        stdscr.refresh()
    curses.curs_set(0)  # Hide cursor
    return inp

def show_help(stdscr):
    """
    Displays a help menu with keybinds and instructions to the user.

    :param stdscr: The curses window object where the help menu is displayed.
    :type stdscr: curses window object
    :return: None
    """
    help_text = [
        "Keybinds:",
        "  Arrow keys: Move selection",
        "  a: Add card",
        "  d: Delete card",
        "  e: Edit card",
        "  m: Move card right",
        "  b: Move card left",
        "  c: Add column",
        "  [: Move column left",
        "  ]: Move column right",
        "  -: Delete Column"
        "  s: Save board",
        "  o: Open board",
        "  z: Undo",
        "  x: Redo",
        "  p: Change card priority",
        "  h: Show this help menu",
        "  q: Quit",
        "Press any key to return..."
    ]

    height, width = stdscr.getmaxyx()
    win_height = len(help_text) + 2
    win_width = max(len(line) for line in help_text) + 4
    win = curses.newwin(win_height, win_width, (height - win_height) // 2, (width - win_width) // 2)
    win.box()

    for idx, line in enumerate(help_text):
        win.addstr(idx + 1, 2, line)
    win.refresh()
    win.getch()

def show_settings(stdscr):
    #TODO: Fix settings menu
    #This will be temporarily disabled

    global current_theme, folder_path
    height, width = stdscr.getmaxyx()

    themes = ['default', 'dark_blue']
    current_theme_index = themes.index(current_theme)
    settings_options = [
        f"Color Theme: {current_theme.replace('_', ' ').title()}",
        f"Save Location: {folder_path}",
        "Back"
    ]

    while True:
        # Step 1: Re-render the settings options list each time the loop runs

        selected_option = 0
        settings_options = [
            f"Color Theme: {current_theme.replace('_', ' ').title()}",
            f"Save Location: {folder_path}",
            "Back"
        ]

        stdscr.clear()
        title = "Settings"
        stdscr.addstr(height // 2 - 5, (width - len(title)) //  2, title, curses.A_BOLD)

        for i, option in enumerate(settings_options):
            x = (width - len(option)) // 2
            y = height // 2 - 2 + i
            if i == selected_option:
                stdscr.addstr(y, x, option, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x, option)

        stdscr.refresh()
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k')):
            selected_option = (selected_option - 1) % len(settings_options)
        elif key in (curses.KEY_DOWN, ord('j')):
            selected_option = (selected_option + 1) % len(settings_options)
        elif key in (curses.KEY_ENTER, 10, 13):
            if selected_option == 0: #Color
                current_theme_index = (current_theme_index + 1) % len(themes)
                current_theme = themes[current_theme_index]
                init_colors()
            elif selected_option == 1: #Save location
                new_path = get_input(stdscr, height - 2, 0, f"New save path (current: {folder_path}): ", width -20)
                if new_path and os.path.isdir(new_path):
                    folder_path = new_path
                    stdscr.addstr(height - 1, 0, "Save path updated. Press any key")
                    stdscr.getch()
                elif new_path:
                    stdscr.addstr(height - 1, 0, "Invalid path. Press any key")
                    stdscr.getch()
            elif selected_option == 2: #Back
                return

def show_startup_screen(stdscr):
    """
    Display the startup screen for the app. It has three options New Board, Open Board, and Quit

    :param stdscr: The curses window object used for rendering the terminal interface.
    :type stdscr: curses.window
    :return: The user's selected option. Returns "new" for creating a new board,
        "open" for opening an existing board, "settings" for opening settings, and "quit" for exiting the application.
    :rtype: str
    """
    height, width = stdscr.getmaxyx()

    options = ["New Board", "Open Board", "Quit"]
    selected_option = 0

    while True:
        stdscr.clear()
        title = "Welcome to TermiKanban!"
        stdscr.addstr(height // 2 -4, (width - len(title)) // 2, title, curses.A_BOLD)
        stdscr.addstr(height // 2 - 2, (width - len("Use arrow keys to navigate, Enter to select")) // 2,
                      "Use arrow keys to navigate, Enter to select")

        for i, option in enumerate(options):
            x = (width - len(option)) // 2
            y = height // 2 + i
            if i == selected_option:
                stdscr.addstr(y, x, option, curses.A_REVERSE)
            else:
                stdscr.addstr(y, x , option)

        stdscr.refresh()
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k')):
            selected_option = (selected_option - 1) % len(options)
        elif key in (curses.KEY_DOWN, ord('j')):
            selected_option = (selected_option + 1) % len(options)
        elif key in (curses.KEY_ENTER, 10, 13):
            if options[selected_option] == "New Board":
                return "new"
            elif options[selected_option] == "Open Board":
                return "open"
            #elif options[selected_option] == "Settings":
                #return "settings"
            elif options[selected_option] == "Quit":
                return "quit"
        elif key == 27: #ESC key
            return "quit"

def create_default_board(board):
    """
    Create The default board
    :param board: The KanbanBoard class
    :return:
    """
    board.add_column("To Do")
    board.add_column("In Progress")
    board.add_column("Done")
    board.add_card(0, "Task 1", "Press H for Help", 3)
    board.add_card(1, "Task 2", "Press 'E' to edit me!")
    board.add_card(2, "Task 3", "Issue? Report it at https://github.com/armadillomike/termikanban/issues")

def main(stdscr):
    """
    Main entry point for the TermiKanban application.

    This function initializes and runs the interactive Kanban board application
    using the curses library. It sets up the environment, handles loading and
    saving functionality, and processes user interactions, including adding,
    editing, and moving cards and columns. This implementation supports undo/redo
    functionality, multiple priority levels for cards, and file management.

    :param stdscr: The curses screen object providing the main window for the
                   application.
    :type stdscr: Any
    :return: None
    """
    # Create the directory in which the boards are saved in
    try:
        os.makedirs(folder_path, exist_ok=True)
    except Exception as e:
        stdscr.addstr(15, 0, f"An error occurred while creating folder: {e}. Try restarting the app")

    # Initialize color pairs for priority levels
    curses.start_color()
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Low priority
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Medium priority
    curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)  # High priority

    board = KanbanBoard()
    selected_col = 0
    selected_card = 0
    current_board_file = None # Step 1: Initialize variable to store the current file path

    # Allows opening of .kanban files through the file explorer
    if len(sys.argv) > 1:
        file_to_open = sys.argv[1]
        if os.path.exists(file_to_open) and file_to_open.endswith(".kanban"):
            try:
                board.load(file_to_open)
                current_board_file = file_to_open
                selected_col = 0 # Reset selection after loading
                selected_card = 0 # Reset selection after loading
            except Exception as e:
                stdscr.addstr(15, 0, f"Error loading file {file_to_open}: {e}")
                stdscr.addstr(16, 0, "Press any ket to continue with a new board...")
                stdscr.getch()
                # If loading the file failed start a new default board
                board = KanbanBoard()
                create_default_board(board)
                selected_col = 0 # Reset selection after creating default
                selected_card = 0 # Reset selection after creating default
        else:
            stdscr.addstr(15, 0, f"Invalid or Nonexistent file: {file_to_open}")
            stdscr.addstr(16, 0, "Press any key to continue to default board...")
            stdscr.getch()
            #If the file is invalid show startup screen
            action = show_startup_screen(stdscr)
            if action == "new":
                board = KanbanBoard()
                create_default_board(board)
                selected_col = 0 # Reset selection
                selected_card = 0 # Reset selection
            elif action == "open":
                file_path = file_picker(stdscr)
                if file_path:
                    board = KanbanBoard()
                    board.load(file_path)
                    current_board_file = file_path
                    selected_col = 0 # Reset selection
                    selected_card = 0 # Reset selection
                else: #If user canceled picker, default to a new board
                    board = KanbanBoard()
                    create_default_board(board)
                    selected_col = 0 # Reset selection
                    selected_card = 0 # Reset selection
            elif action == "quit":
                return #Exit the app


    else:
        #If no argument, show startup screen
        action = show_startup_screen(stdscr)
        if action == "new":
            board = KanbanBoard()
            create_default_board(board)
            selected_col = 0 # Reset selection
            selected_card = 0 # Reset selection
        elif action == "open":
            file_path = file_picker(stdscr)
            if file_path:
                board = KanbanBoard()
                board.load(file_path)
                current_board_file = file_path
                selected_col = 0 # Reset selection
                selected_card = 0 # Reset selection
            else: #User cancelled picker, create default board
                board = KanbanBoard()
                create_default_board(board)
                selected_col = 0 # Reset selection
                selected_card = 0 # Reset selection
        #elif action == "settings":
            #show_settings(stdscr)
            # After returning from settings, re-evaluate the board state
            # and ensure selections are valid, especially if theme changed
            # and colors need re-initialization.
            #init_colors() # Re-initialize colors in case theme changed
            # No need to reset selected_col/card here unless settings could modify board
        elif action == "quit":
            return #Exit the app

    # Initialize undo and redo stacks
    undo_stack = []
    redo_stack = []

    #Ensure the selected col and card are valid for the new or loaded board
    # This block is crucial for preventing IndexError after board changes
    if board.columns:
        selected_col = min(selected_col, len(board.columns) - 1)
        if board.columns[selected_col].cards:
            selected_card = min(selected_card, len(board.columns[selected_col].cards) - 1)
        else:
            selected_card = 0
    else: # If the board is completely empty, reset selections
        selected_col = 0
        selected_card = 0


    def snapshot():
        undo_stack.append(copy.deepcopy(board))
        redo_stack.clear()

    # Main event loop
    while True:
        # Ensure selected_col and selected_card are always valid before drawing
        if not board.columns:
            selected_col = 0
            selected_card = 0
        else:
            selected_col = max(0, min(selected_col, len(board.columns) - 1))
            if not board.columns[selected_col].cards:
                selected_card = 0
            else:
                selected_card = max(0, min(selected_card, len(board.columns[selected_col].cards) - 1))

        draw_board(stdscr, board, selected_col, selected_card)
        key = stdscr.getch()

        if key in (ord('a'), ord('d'), ord('e'), ord('c'), ord('m'), ord('b'), ord('['), ord(']')):
            snapshot()

        if key == ord('q'):
            stdscr.addstr(15, 0, "Save before exit? (y/n): ")
            stdscr.refresh()
            confirm = stdscr.getch()
            if confirm in (ord('y'), ord('Y')):
                # Step 4: Modify quit logic to save to current_board_file if it exists
                if current_board_file:
                    board.save(current_board_file)
                    stdscr.addstr(17, 0, f"Board saved to {os.path.basename(current_board_file)}. Press any key.")
                    stdscr.getch()
                else:
                    save_name = get_input(stdscr, 16, 0, "Filename:", 10)
                    if save_name:
                        save_path = os.path.join(folder_path, f"{save_name}.kanban")
                        board.save(save_path)
                        current_board_file = save_path # Update current_board_file
                        stdscr.addstr(17, 0, f"Board saved as {save_name}.kanban. Press any key.")
                        stdscr.getch()
                break
            elif confirm in (ord('n'), ord('N')):
                break
            stdscr.clear()

        elif key == curses.KEY_RIGHT and board.columns and selected_col < len(board.columns) - 1:
            selected_col += 1
            selected_card = 0
        elif key == curses.KEY_LEFT and selected_col > 0:
            selected_col -= 1
            selected_card = 0
        elif key == curses.KEY_DOWN and board.columns and board.columns[selected_col].cards and selected_card < len(board.columns[selected_col].cards) - 1:
            selected_card += 1
        elif key == curses.KEY_UP and board.columns and board.columns[selected_col].cards and selected_card > 0:
            selected_card -= 1

        elif key == ord('m'):
            if board.columns and selected_col < len(board.columns) - 1 and board.columns[selected_col].cards:
                card = board.columns[selected_col].cards.pop(selected_card)
                board.columns[selected_col + 1].cards.append(card)
                # Adjust selected_card if the column it was in is now empty or card count changed
                if selected_card >= len(board.columns[selected_col].cards):
                    selected_card = max(0, len(board.columns[selected_col].cards) - 1)
                selected_col += 1
        elif key == ord('b'):
            if board.columns and selected_col > 0 and board.columns[selected_col].cards:
                card = board.columns[selected_col].cards.pop(selected_card)
                board.columns[selected_col - 1].cards.append(card)
                # Adjust selected_card if the column it was in is now empty or card count changed
                if selected_card >= len(board.columns[selected_col].cards):
                    selected_card = max(0, len(board.columns[selected_col].cards) - 1)
                selected_col -= 1

        # Card management
        elif key == ord('d'):  # Delete card
            if board.columns and board.columns[selected_col].cards:
                board.columns[selected_col].cards.pop(selected_card)
                if selected_card >= len(board.columns[selected_col].cards):
                    selected_card = max(0, len(board.columns[selected_col].cards) - 1)
        elif key == ord('a'):  # Add card
            # Ensure there's at least one column to add a card to
            if not board.columns:
                stdscr.addstr(15, 0, "No columns to add cards to. Add a column first (press 'c'). Press any key.")
                stdscr.getch()
                stdscr.clear()
                continue

            title = get_input(stdscr, 15, 0, "Title: ", 20)
            description = get_input(stdscr, 16, 0, "Description: ", 40)
            priority_str = get_input(stdscr, 17, 0, "Priority (1=Low, 2=Med, 3=High): ", 1)
            priority = int(priority_str) if priority_str in ("1", "2", "3") else 1
            board.add_card(selected_col, title, description, priority) # Add to currently selected column
            selected_card = len(board.columns[selected_col].cards) - 1 # Select the newly added card
        elif key == ord('e'):  # Edit card
            if board.columns and board.columns[selected_col].cards:
                card = board.columns[selected_col].cards[selected_card]
                new_title = get_input(stdscr, 15, 0, f"Edit Title ({card.title}): ", 20)
                new_description = get_input(stdscr, 16, 0, f"Edit Description ({card.description}): ", 40)
                card.title = new_title if new_title else card.title
                card.description = new_description if new_description else card.description
                stdscr.clear()

        # Board management
        elif key == ord('s'):  # Save board
            # Step 3: Modify save logic
            if current_board_file:
                board.save(current_board_file)
                stdscr.addstr(15, 0, f"Board saved to {os.path.basename(current_board_file)}. Press any key.")
                stdscr.getch()
            else:
                save_name = get_input(stdscr, 15, 0, "Filename:", 10)
                if save_name:
                    save_path = os.path.join(folder_path, f"{save_name}.kanban")
                    board.save(save_path)
                    current_board_file = save_path # Update current_board_file
                    stdscr.addstr(17, 0, f"Board saved as {save_name}.kanban. Press any key.")
                    stdscr.getch()
            stdscr.clear()
        elif key == ord('o'):  # Open board
            file_path = file_picker(stdscr)
            if file_path:
                try:
                    board = KanbanBoard()
                    board.load(file_path)
                    current_board_file = file_path # Step 2: Update current_board_file on load
                    selected_col = 0 # Reset selection after loading
                    selected_card = 0 # Reset selection after loading
                except Exception as e:
                    stdscr.addstr(15, 0, f"Error loading file {file_path}: {e}. Press any key.")
                    stdscr.getch()
                    # If loading fails, revert to the previous board state or a new default one
                    if undo_stack:
                        board = undo_stack[-1] # Revert to last known good state
                    else:
                        board = KanbanBoard()
                        create_default_board(board)
                    selected_col = 0
                    selected_card = 0
            stdscr.clear()
        elif key == ord('c'):  # Add column
            col_name = get_input(stdscr, 15, 0, "New column name: ", 20)
            if col_name:
                board.add_column(col_name)
                selected_col = len(board.columns) - 1
                selected_card = 0
            stdscr.clear()

        # Column Management
        elif key == ord('-'):  # Delete card
            if board.columns and board.columns[selected_col].cards:
                board.columns[selected_col].cards.pop(selected_card)
                if selected_card >= len(board.columns[selected_col].cards):
                    selected_card = max(0, len(board.columns[selected_col].cards) - 1)
        elif key == ord('['):  # Move column left
            if selected_col > 0:
                board.columns[selected_col - 1], board.columns[selected_col] = board.columns[selected_col], \
                    board.columns[selected_col - 1]
                selected_col -= 1
        elif key == ord(']'):  # Move column right
            if selected_col < len(board.columns) - 1:
                board.columns[selected_col + 1], board.columns[selected_col] = board.columns[selected_col], \
                    board.columns[selected_col + 1]
                selected_col += 1

        # Undo/Redo
        elif key == ord('z'):  # Undo
            if undo_stack:
                redo_stack.append(copy.deepcopy(board))
                board = undo_stack.pop()
                # Re-validate selections after undo
                if board.columns:
                    selected_col = min(selected_col, len(board.columns) - 1)
                    if board.columns[selected_col].cards:
                        selected_card = min(selected_card, len(board.columns[selected_col].cards) - 1)
                    else:
                        selected_card = 0
                else:
                    selected_col = 0
                    selected_card = 0
        elif key == ord('x'):  # Redo
            if redo_stack:
                undo_stack.append(copy.deepcopy(board))
                board = redo_stack.pop()
                # Re-validate selections after redo
                if board.columns:
                    selected_col = min(selected_col, len(board.columns) - 1)
                    if board.columns[selected_col].cards:
                        selected_card = min(selected_card, len(board.columns[selected_col].cards) - 1)
                    else:
                        selected_card = 0
                else:
                    selected_col = 0
                    selected_card = 0

        # Other functions
        elif key == ord('p'):  # Change priority
            if board.columns and board.columns[selected_col].cards:
                card = board.columns[selected_col].cards[selected_card]
                card.priority = card.priority % 3 + 1
        elif key == ord('h'):  # Show help
            show_help(stdscr)
        elif key == ord('r'): #Show settings
            show_settings(stdscr)
            init_colors() # Re-initialize colors in case theme changed


if __name__ == "__main__":
    curses.wrapper(main)