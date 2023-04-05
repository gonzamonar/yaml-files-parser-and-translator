import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import askdirectory
from googletrans import Translator
from yaml import CLoader as Loader
import yaml
import csv
import googletrans
import json
import os
import re
import requests
import threading

###################################### FUNCTIONS ######################################

def main_execute():
    if option.get() == 1:
        filepath = txt_file.get()
        translate(get_root_path(filepath), get_filename(filepath))
    elif option.get() == 2:
        folderpath = txt_folder.get()
        for _, _, file_names in os.walk(folderpath):
            for filename in file_names:
                translate(folderpath, filename)


def translate(root: str, filename: str):
    if filename.endswith(".yaml"):
        update_log(f"[Translating...] {filename}")
        filename = filename.split(".yaml")[0]

        convert_yaml_to_txt(f"{root}/{filename}.yaml")
        create_yaml_cleanedlist(root, filename)
        translate_txt(f"{root}/{filename}.txt")
        update_log(f"[Finished] {filename}.yaml")
    else:
        update_log(f"[Error: not an YAML file] {filename}")


def convert_yaml_to_txt(yamlpath: str):
    with open(yamlpath, "r", encoding="utf-8") as yamlfile:
        try:
            object = yaml.load(yamlfile, Loader)
            with open("buffer.txt", "w", encoding="utf-8") as file:
                file.write(str(object))
        except yaml.YAMLError:
            update_progress(f"[Error converting YAML file to txt.]")


def create_yaml_cleanedlist(root: str, filename: str):
    ACCEPTED = get_accepted_keywords()
    cleaned_yaml = []
    with open("buffer.txt", "r", encoding="utf-8") as file:
        try:
            for line in file:
                coincidences = re.findall(r"'[^']+': '[^']+'", line)
                for item in coincidences:
                    for w in ACCEPTED:
                        p = re.compile("'"+ w + "':")
                        good_keyword = p.search(item)
                        if good_keyword:
                            cleaned_yaml.append(item)
                            coincidences.remove(item)
                save_leftovers(coincidences, root, filename)
                refine_yaml_cleanedlist(cleaned_yaml, root, filename)

        except Exception as e:
            print(e)
            update_progress(f"[Error cleaning YAML list.]")
            

def get_accepted_keywords():
    try:
        keywords = []
        with open('keywords.csv', mode='r', encoding="utf-8") as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                keywords.append(row[0])
        return keywords
    except FileNotFoundError:
        update_progress(f"[Error keywords CSV empty.]")
        basic_keywords = ["title", "description", "summary", "text", "alt", "caption", "tasks"]
        file = open('keywords.csv', mode='w', encoding="utf-8")
        for kword in basic_keywords:
            file.write(kword + "\n")
        file.close()
        return basic_keywords


def save_leftovers(leftovers: list, root: str, filename: str):
    with open(f'{root}/leftovers_{filename}.txt', "w", encoding="utf-8") as txtfile:
        for item in leftovers:
            txtfile.write(item + "\n")


def refine_yaml_cleanedlist(cleanedlist: list, root: str, filename: str):
    with open('2nd_buffer.txt', "w", encoding="utf-8") as txtfile:
        for line in cleanedlist:
            line = line.split("': '")[1][:-1]
            line = line.replace("\n", " ")
            line = re.sub(r"\.[\s]", ".\n", line)
            line = re.sub(r"\.$", ".\n", line)
            line = line.replace("!", "!\n")
            line = line.replace("?", "?\n")
            line = line.strip()
            txtfile.write(line + "\n")


def translate_txt(dest_path: str):
    translator = Translator()
    src_lang = get_selected_language(cmb_fromlang)
    dest_lang = get_selected_language(cmb_tolang)
    
    with open("2nd_buffer.txt", "r", encoding="utf-8") as file:
        txt_file = open(dest_path, "w", encoding="utf-8")
        c = 1
        for line in file:
            update_progress(f"Translating line Nº{c}.")
            try:
                line = line.strip()
                trans_line = translator.translate(line, dest=dest_lang, src=src_lang).text
                txt_file.write(line + '\n')
                txt_file.write(trans_line + '\n\n')
            except:
                txt_file.write(line + '\n')
                txt_file.write("[ERROR] It occurred an error while translating this line." + '\n\n')
                update_log(f"Translation error on line {c}")
                continue
            c += 1
        update_progress(f"All {c} lines translated.")
        txt_file.close()

    os.remove("buffer.txt")
    os.remove("2nd_buffer.txt")


def get_root_path(path: str):
    split_path = path.split("/")
    root = "".join(f"{s}/" for s in split_path[0:-1])
    return root


def get_filename(path: str):
    split_path = path.split("/")
    return split_path[-1]


def update_log(log: str):
    lbl_log.config(text=log)


def update_progress(log: str):
    lbl_progress.config(text=log)


def set_execution_mode():
    if option.get() == 1:
        txt_file.config(state="normal")
        btn_file_explorer.config(state="normal")
        txt_folder.delete(0, 'end')
        txt_folder.config(state="disabled")
        btn_folder_explorer.config(state="disabled")
    elif option.get() == 2:
        txt_file.delete(0, 'end')
        txt_file.config(state="disabled")
        btn_file_explorer.config(state="disabled")
        txt_folder.config(state="normal")
        btn_folder_explorer.config(state="normal")


def explore_file():
    txt_file.delete(0, 'end')
    tk.Tk().withdraw()
    filepath = askopenfilename()
    txt_file.insert(0, filepath)


def explore_folder():
    txt_folder.delete(0, 'end')
    tk.Tk().withdraw()
    dirpath = askdirectory()
    txt_folder.insert(0, dirpath)


def get_selected_language(cmb: ttk.Combobox):
    selected = "auto"
    if(cmb.get() != selected):
        selected = googletrans.LANGCODES[cmb.get()]
    return selected


def create_json_config():
    with open("config.json", "w", encoding="utf-8") as jsonfile:
        jsonfile.write(
    """
    {
        "window_icon_name" : "yaml-icon.ico",
        "window_icon_url" : "https://raw.githubusercontent.com/gonzamonar/Resources/master/yaml-icon.ico",
        "explorer_img_name" : "file-explorer.png",
        "explorer_img_url" : "https://raw.githubusercontent.com/gonzamonar/Resources/master/file-explorer.png",
        "last_orig_language": "english",
        "last_dest_language": "korean",
        "window_size" : "300x420"
    }
    """
    )


def read_json_config():
    with open("config.json", "r", encoding="utf-8") as jsonfile:
        config = json.load(jsonfile)
    return config


def fetch_file(url: str, filename: str):
    try:
        image_url = url
        img_data = requests.get(image_url).content
        with open(filename, 'wb') as handler:
            handler.write(img_data)
    except tk.TclError:
        pass


def update_jsonconfig(key: str, value: str):
    config[key] = value
    json_obj = json.dumps(config)
    with open("config.json", "w", encoding="utf-8") as jsonfile:
        jsonfile.write(json_obj)


def program_exit():
    window.quit()
    window.destroy()


###################################### USER INTERFACE ######################################
FONT = ("", "9", "bold")
LANG = [l for l in googletrans.LANGCODES.keys()]
LANG.insert(0, "auto")

## LOADING & VERIFYING RESOURCES ##
if not os.path.exists("config.json"):
    create_json_config()

try:
    config = read_json_config()
except FileNotFoundError:
    create_json_config()
    try:
        config = read_json_config()
    except FileNotFoundError:
        normal_init = False

if not os.path.exists(config["window_icon_name"]):
    fetch_file(config["window_icon_url"], config["window_icon_name"])

if not os.path.exists(config["explorer_img_name"]):
    fetch_file(config["explorer_img_url"], config["explorer_img_name"])


### WINDOW INIT ###
window = tk.Tk()
window.title("YAML Translator")
window.geometry(config["window_size"])
window.resizable(False, False)
try:
    window.iconbitmap(config["window_icon_name"])
except tk.TclError:
    pass

if os.path.exists(config["explorer_img_name"]):
    img_explorer = PhotoImage(file=config["explorer_img_name"])
else:
    img_explorer = None


### FRAME 1 - MODE SELECTION ###
frame1 = tk.Frame(window)
frame1.grid(row=0, column=0)

lbl_rdobtn = tk.Label(frame1, text="Execution mode: ")
lbl_rdobtn.grid(row=0, column=0, padx=10, pady=10)

option = tk.IntVar()
rdo_file = tk.Radiobutton(frame1, text="File", variable=option, value=1, command=set_execution_mode)
rdo_folder = tk.Radiobutton(frame1, text="Folder", variable=option, value=2, command=set_execution_mode)
rdo_file.grid(row=0, column=1, padx=10, pady=10)
rdo_folder.grid(row=0, column=2, padx=10, pady=10)
rdo_file.select()


### FRAME 2 - FILE SELECTION ###
frame2 = tk.Frame(window)
frame2.grid(row=1, column=0)

lbl_section2 = tk.Label(frame2, text="File/s selection", font=FONT)
lbl_section2.grid(row=0, columnspan=2, padx=5, pady=(10, 0))

lbl_file = tk.Label(frame2, text="File path: ")
lbl_file.grid(row=1, column=0, padx=5, pady=5, sticky="e")
txt_file = tk.Entry(frame2, width=25, state="normal")
txt_file.grid(row=1, column=1, padx=5, pady=5)

lbl_folder = tk.Label(frame2, text="Folder path: ")
lbl_folder.grid(row=2, column=0, padx=5, pady=5, sticky="e")
txt_folder = tk.Entry(frame2, width=25, state="disabled")
txt_folder.grid(row=2, column=1, padx=5, pady=5)

    #· EXPLORER BTN IMG ·#
img_label = tk.Label(image=img_explorer)
btn_file_explorer = tk.Button(frame2, image=img_explorer, command=explore_file, borderwidth=0, state="normal")
btn_file_explorer.grid(row=1, column=3, padx=5, pady=5)

btn_folder_explorer = tk.Button(frame2, image=img_explorer, command=explore_folder, borderwidth=0, state="disabled")
btn_folder_explorer.grid(row=2, column=3, padx=5, pady=5)


### FRAME 3 - LANGUAGE SELECTION ###
frame3 = tk.Frame(window)
frame3.grid(row=2, column=0)

lbl_section3 = tk.Label(frame3, text="Language selection", font=FONT)
lbl_section3.grid(row=0, columnspan=2, padx=5, pady=(15, 0))

lbl_fromlang = tk.Label(frame3, text="Origin: ", width=12, anchor="e")
lbl_fromlang.grid(row=1, column=0, padx=5, pady=5)
cmb_fromlang = ttk.Combobox(frame3, state="readonly", values=LANG, width=20)
cmb_fromlang.current(LANG.index(config["last_orig_language"]))
cmb_fromlang.grid(row=1, column=1, padx=5, pady=5)
cmb_fromlang.bind("<<ComboboxSelected>>", lambda _ : update_jsonconfig("last_orig_language", cmb_fromlang.get()))

lbl_tolang = tk.Label(frame3, text="Destination: ", width=12, anchor="e")
lbl_tolang.grid(row=2, column=0, padx=5, pady=5)
cmb_tolang = ttk.Combobox(frame3, state="readonly", values=LANG, width=20)
cmb_tolang.current(LANG.index(config["last_dest_language"]))
cmb_tolang.grid(row=2, column=1, padx=5, pady=5)
cmb_tolang.bind("<<ComboboxSelected>>", lambda _ : update_jsonconfig("last_dest_language", cmb_tolang.get()))


### SECTION 4 - LOGGER ###
lbl_section3 = tk.Label(window, text="Progress Log", font=FONT)
lbl_section3.grid(row=4, columnspan=2, padx=5, pady=(20, 5))
lbl_log = tk.Label(window, text="", width=35, bg="#FFFFFF", anchor="w")
lbl_log.grid(row=5, column=0, padx=10, pady=(0, 5))
lbl_progress = tk.Label(window, text="", width=35, bg="#FFFFFF", anchor="w")
lbl_progress.grid(row=6, column=0, padx=10, pady=(0, 5))


### SECTION 5 - SUBMIT ###
btn_submit = tk.Button(window, text="TRANSLATE", width=35, bg="#FFFFFF", command= lambda : threading.Thread(target=main_execute).start() )
btn_submit.grid(row=7, columnspan=2, padx=10, pady=25)


## MAIN LOOP ##
window.protocol("WM_DELETE_WINDOW", program_exit)
window.mainloop()
