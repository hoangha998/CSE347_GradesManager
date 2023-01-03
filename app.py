import pandas as pd
import math
from collections import defaultdict
from copy import deepcopy
from GradesManager import GradesManager


import tkinter as tk
import tkinter.font as tkFont
from tkinter.filedialog import askopenfilename
from ttkwidgets.autocomplete import AutocompleteCombobox

class App:
    def __init__(self, root):
        self.root = root
        #setting title
        root.title("CSE 347 Homework Grades Monitor")
        #setting window size
        self.width=600
        self.height=600
        self._update_window_size()
        
        # Homework number
        hw_no_label=tk.Label(root, text= "Homework number:")
        hw_no_label.place(x=40,y=40,width=120,height=25)

        self.hw_no_entry=tk.Entry(root, text= "Enter number", justify='center')
        self.hw_no_entry.place(x=160,y=40,width=50,height=25)

        
        # Raw grade selector
        rawgrade_label=tk.Label(root, justify='left', anchor="w")
        rawgrade_label["text"] = "Raw excel grade file (from Gradescope):"
        rawgrade_label.place(x=40,y=80,width=220,height=25)

        rawgrade_button=tk.Button(root, text= "Select File")
        rawgrade_button.place(x=270,y=80,width=70,height=25)
        rawgrade_button["command"] = self.select_raw_grade_file_command
        
        
        # Canvas gradebook selector
        canvas_label=tk.Label(root, justify='left', anchor="w")
        canvas_label["text"] = "Canvas gradebook file (latest version):"
        canvas_label.place(x=40,y=120,width=220,height=25)

        canvas_label=tk.Button(root, text= "Select File")
        canvas_label.place(x=270,y=120,width=70,height=25)
        canvas_label["command"] = self.select_canvas_gradebook_file_command

        # Submit button
        self.submit_button=tk.Button(root, text= "Reformat Grade File")
        self.submit_button.place(x=40,y=500,width=150,height=25)
        self.submit_button["command"] = self.reformat_grades   
        
        
        self.status_line1 = tk.Label(root, text= "Please select a grade file", fg="#0f6328", justify='left', anchor="w")
        self.status_line1.place(x=40,y=535,width=550,height=25)
        self.status_line2 = tk.Label(root, text='', fg="#0f6328", justify='left', anchor="w")
        self.status_line2.place(x=40,y=570,width=550,height=25)
    
        
        # hidden vars to reformat grades
        self.P1_weights_entries = []
        self.P2_weights_entries = []
        self.weights_labels = []
        self.raw_grades = None
        self.canvas_gradebook_path = None
        self.extensions = [] # just for the UI
        self.items_below_extension_section = [self.submit_button, self.status_line1, self.status_line2]
        self.extension_cases = defaultdict(lambda:0) # store this to use when reformat grades

    def _update_window_size(self):
        screenwidth = self.root.winfo_screenwidth()
        screenheight = self.root.winfo_screenheight()
        alignstr = '%dx%d+%d+%d' % (self.width, self.height, (screenwidth - self.width) / 2, (screenheight - self.height) / 2)
        root.geometry(alignstr)
        root.resizable(width=False, height=False)

    
    def _move_items_below_extension_section(self, dir):
        offset = -35 if dir == "up" else 35
        for item in self.items_below_extension_section:
            new_y = item.winfo_y() + offset
            item.place(y=new_y)
            if new_y >= self.height-35:
                self.height += 100
                self._update_window_size()


    def add_extension_case(self):
        full_name_with_id = self.student_name_entry.get().strip()
        extra_days = self.extension_entry.get()
        student_id = int(full_name_with_id.split(' ')[-1].strip('()'))

        # Validate inputs
        if full_name_with_id == "" or extra_days == "":
            self._raise_invalid_inputs("Invalid extension case input. Please fill out all fields.")
        try:
            if float(extra_days) != int(extra_days):
                self._raise_invalid_inputs("Invalid extension case input. Days must be an integer.")
                return
        except:
            self._raise_invalid_inputs("Invalid extension case input. Days must be an integer.")
            return
        if self.extension_cases[student_id] != 0:
            self._raise_invalid_inputs("Extensions were already added for this student.")
            return    
        if student_id not in self.raw_grades['SID'].values:
            self._raise_invalid_inputs("Student not found. Please use the autocomplete feature.")
            return

        
        if len(self.extensions) == 0:
            id = 0
            y = 300
        else:
            id = self.extensions[-1]['id']+1
            last_item_id = self.extensions[-1]['id']
            last_item_y = self.root.nametowidget("case_{}".format(last_item_id)).winfo_y()
            y = last_item_y + 35

        self.extensions.append({'id':id, 'name':full_name_with_id, 'days': extra_days})

        added_case = tk.Label(root, text="{}, {} days".format(full_name_with_id, extra_days), fg="#888", name='case_{}'.format(id))
        added_case.place(x=60, y=y, height=25, width=200)
        remove_button = tk.Button(root, text="Remove", name='button_{}'.format(id))
        remove_button.place(x=280, y=y, height=25, width=60)

        if y+35 >= self.submit_button.winfo_y():
            self._move_items_below_extension_section(dir="down")
        
        
        def listener_remove_extension_case(id):
            def remove_extension_case():
                for item_to_move in self.extensions:
                    if item_to_move['id'] <= id:
                        continue
                    case_to_move = self.root.nametowidget("case_{}".format(item_to_move['id']))
                    button_to_move =  self.root.nametowidget("button_{}".format(item_to_move['id']))
                    case_to_move.place(y=case_to_move.winfo_y() - 35)
                    button_to_move.place(y=button_to_move.winfo_y() - 35)

                case_to_remove = self.root.nametowidget("case_{}".format(id))
                button_to_remove = self.root.nametowidget("button_{}".format(id))
                case_to_remove.destroy()
                button_to_remove.destroy()    
                for item in self.extensions:
                    if item['id'] == id:
                        self.extensions.remove(item)
                        break 
            return remove_extension_case

        remove_button['command'] = listener_remove_extension_case(id)

        # save student & extension
        
        self.extension_cases[student_id] = int(extra_days)

        #clear inputs
        self.student_name_entry['text'] = ''
        self.extension_entry['text'] = ''


    def select_raw_grade_file_command(self):
        filename = askopenfilename()
        if filename.split('.')[-1] != 'xlsx': # validate input file is .xlsx
            self._raise_invalid_inputs('Raw grade file must be of type ".xlsx" (Excel file)')
            return
        filename_label = tk.Label(root, text= '...' + filename[-33:], justify='left', anchor="w", fg="#00f")
        filename_label.place(x=360,y=80,width=210,height=25)
        self.load_raw_grade_file(filename)
    
    
    def select_canvas_gradebook_file_command(self):
        filename = askopenfilename()
        if filename.split('.')[-1] != 'csv': # validate input file is .xlsx
            self._raise_invalid_inputs('Canvas gradebook file must be of type ".csv"')
            return
        filename_label = tk.Label(root, text= '...' + filename[-33:], justify='left', anchor="w", fg="#00f")
        filename_label.place(x=360,y=120,width=210,height=25)
        self.canvas_gradebook_path = filename 
        
    
    def load_raw_grade_file(self, raw_grades_path): # raw grades from gradescope
        # update status line
        self.status_line1['text'] = 'Loading raw grade file...'
        self.status_line2['text'] = ''
        
        # reset weight inputs
        for entry in self.P1_weights_entries + self.P2_weights_entries + self.weights_labels:
            entry.destroy()
        
        self.raw_grades = pd.read_excel(raw_grades_path)
        
        # Count number of parts for each of the 2 problem P1, P2
        self.P1_num_parts = 0
        self.P2_num_parts = 0
        for col in self.raw_grades.columns[13:]: # Index 13 is always where actual grades start
            if col[0] == '1':
                self.P1_num_parts += 1
            elif col[0] == '2':
                self.P2_num_parts += 1
                
        
        # Ask for the weight of each part in the GUI
        part_labels = ['a','b','c','d','e','f','g','h','i','j','k']
        
        self.weights_labels = [] # use to clear labels for new homework run
        self.P1_weights_entries = []
        self.P2_weights_entries = []
        
        # Problem 1 weights
        p1_weights_label=tk.Label(root, text= "Problem 1 weights:")
        p1_weights_label.place(x=60,y=160,width=115,height=25)
        if self.P1_num_parts == 1:
            p1_weights_na=tk.Label(root, justify='center', text='1.0 (only 1 part)', fg="#888")
            p1_weights_na.place(x=180,y=160,width=100,height=25)
        else:
            x_offset = 0
            for part in range(self.P1_num_parts):
                cur_x = 180 + x_offset
                p1_weights_label=tk.Label(root, text= part_labels[part] + ")")
                p1_weights_label.place(x=cur_x,y=160,width=20,height=25)
                p1_weights_entry=tk.Entry(root, justify='center')
                p1_weights_entry.place(x=cur_x+20,y=160,width=30,height=25)
                p1_weights_entry.insert(0, 1/self.P1_num_parts) # default weight
                self.P1_weights_entries.append(p1_weights_entry)
                self.weights_labels.append(p1_weights_label)
                x_offset += 60
                
        # Problem 2 weights
        p2_weights_label=tk.Label(root, text= "Problem 2 weights:")
        p2_weights_label.place(x=60,y=200,width=115,height=25)
        if self.P2_num_parts == 1:
            p2_weights_na=tk.Label(root, justify='center', text='1.0 (only 1 part)', fg="#888")
            p2_weights_na.place(x=180,y=200,width=100,height=25)
        else:
            x_offset = 0
            for part in range(self.P2_num_parts):
                cur_x = 180 + x_offset
                p2_weights_label=tk.Label(root, text= part_labels[part] + ")")
                p2_weights_label.place(x=cur_x,y=200,width=20,height=25)
                p2_weights_entry=tk.Entry(root, justify='center')
                p2_weights_entry.place(x=cur_x+20,y=200,width=30,height=25)
                p2_weights_entry.insert(0, 1/self.P2_num_parts) # default weight
                self.P2_weights_entries.append(p2_weights_entry)
                self.weights_labels.append(p2_weights_label)
                x_offset += 60

        # Load student names for suggestions
        self.student_names = []
        self.extension_cases = defaultdict(lambda:0) # clear in case of a new run
        def extract_name_with_id(row):
            full_name_with_id = "{} {} ({})".format(row['First Name'], row['Last Name'], row['SID'])
            self.student_names.append(full_name_with_id)
        self.raw_grades.apply(extract_name_with_id, axis=1)

        # Add Late days extension to UI
        extension_section = tk.Label(root, text="Extensions")
        extension_section.place(x=40, y=240, height=25)

        student_name_label = tk.Label(root, text="Name:") 
        student_name_label.place(x=60, y=265, height=25)
        self.student_name_entry = AutocompleteCombobox(root, text="", completevalues=self.student_names)
        self.student_name_entry.place(x=120, y=265, height=25, width=150)

        extension_label = tk.Label(root, text="Days:")
        extension_label.place(x=280, y=265, height=25)
        self.extension_entry = tk.Entry(root, text="")
        self.extension_entry.place(x=320, y=265, height=25, width=50) 

        add_button = tk.Button(root, text="Add")
        add_button.place(x=390, y=265, height=25, width=50)
        add_button["command"] = self.add_extension_case

        
        self._display_status_lines('Raw grade file loaded!') 
        
    
    def _display_status_lines(self, line1='', line2=''):
        self.status_line1['fg'] = '#0f6328' # green
        self.status_line2['fg'] = '#0f6328'
        self.status_line1['text'] = line1
        self.status_line2['text'] = line2
    
    def _raise_invalid_inputs(self, line1='', line2=''):
        self.status_line1['fg'] = '#f00' # red
        self.status_line2['fg'] = '#f00'
        self.status_line1['text'] = line1
        self.status_line2['text'] = line2
        
        
    def reformat_grades(self):
        
        self._display_status_lines('Reformatting grades...') 
        
        # =============================================================================
        #         Validate user's inputs
        # =============================================================================
                
        # validate existence of "late_days_history.xlsx
        try:
            # df to keep track of late days across all homework
            late_days_history = pd.read_excel("./Late_days/late_days_used_history.xlsx")
            late_days_history.fillna(0, inplace=True) # students got added to the class later doesn't have past late days --> all 0 
        except:
            self._raise_invalid_inputs("File not found", '"late_days_history.xlsx" is missing')
        
        # validate homework number input
        try: 
            HOMEWORK_NO = int(self.hw_no_entry.get())
        except:
            self._raise_invalid_inputs("Run time error.", "Homework number must be an integer.")
            return
            
        # validate raw homework grade file chosen
        if self.raw_grades is None:
            self._raise_invalid_inputs("File not found", "Please select a raw grade file from gradescope.")
            return
        # validate canvas gradebook file chosen
        if self.canvas_gradebook_path is None:
            self._raise_invalid_inputs("File not found", "Please select a Canvas gradebook file with the latest grades.")
            return
        
        # validate weights inputs
        try:
            # Problem 1 weights
            if self.P1_num_parts == 1:
                P1_weights = [1]
            else:
                P1_weights = [float(entry.get()) for entry in self.P1_weights_entries]
                if sum(P1_weights) != 1:
                    raise ValueError
            
            # Problem 2 weights
            if self.P2_num_parts == 1:
                P2_weights = [1]
            else:
                P2_weights = [float(entry.get()) for entry in self.P2_weights_entries]
                if sum(P2_weights) != 1:
                    raise ValueError
        except:
            self._raise_invalid_inputs("Run time error. Weights must be decimals (e.g 0.2, 0.5)", "And each problem's weights must add up to 1.0")
            return
        
        
        # =============================================================================
        #         Reformat Grades
        # =============================================================================
        gradesManager = GradesManager(self.raw_grades, HOMEWORK_NO, late_days_history, extensions=self.extension_cases)
        gradesManager.reformat_hw_grades(P1_weights, P2_weights, save=True)
        print("Graded reformatted")
        gradesManager.update_historical_late_days_file()
        gradesManager.export_hw_grades_to_canvas_gradebook(self.canvas_gradebook_path)
        
        self._display_status_lines(line1='Grades Reformatted! Late days accounted! "canvas_grades_book.csv" was saved in /Export_forcanvas',
                                  line2='"HW{}_Final_Grades.xlsx" was saved in /Reformatted_grades!'.format(HOMEWORK_NO)
                                  )
        


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
