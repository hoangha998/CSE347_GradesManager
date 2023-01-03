# CSE 347 Grades Manager App

  

## Table of contents

1. [Dependencies](#dependencies)

2. [First-time setup](#first-time-setup)

3. [Usage guidelines](#usage-guidelines)

4. [General notes](#general-notes)

5. [Dev notes](#dev-notes)

## Dependencies
Navigate to the project’s root folder and run:
``` bash
$ python pip install -r requirements.txt
```
> If you run into some errors, you can also try to install each package in `requirements.txt` individually (optionally, using your choice of virtual environment)

Note that if you use Mac/Linux instead of Windows, `tkinter` must be installed differently with:
```bash
$ sudo apt-get install python-tk
```
> The version of Python that I was using was 3.8.10 (other versions might still work)

## First-time setup

At the beginning of every semester, this repo can be cloned fresh to reset everything (grade files, late days history, etc.)

![fresh clone](https://i.ibb.co/PZvBFTH/image.png)

From a terminal, run:
``` bash
$ python initialization.py
```
This will setup the files & folders structure necessary for the grades manager app.

![after running initialization](https://i.ibb.co/Bz9ZMcv/image.png)

## Usage guidelines

To convert a homework’s grades, the first step is to obtaining the raw grade file from Gradescope and the latest Grade book from Canvas:

1.  Navigate to the assignment’s Gradescope page and select “Download grades” (for Excel), download the file and save it in the folder `./Raw_gradescope_grades`
	![Download raw grades from Gradescope](https://i.ibb.co/ZgsNRx8/image.png)
    
2.  From the course Canvas page, go to "Grades" → "Actions" → Export entire gradebook, download it and save it in `./Gradebook_from_canvas`

	![Download latest gradebook](https://i.ibb.co/4jrgcLP/image.png)

Now, run `app.py` either by double clicking on it or open it in a terminal program (e.g. `$ python3 app.py`). You should see an UI like below. Simply fill out the input fields sequentially.

![Sample run](https://i.ibb.co/68P88mp/image.png)

1.  Homework number as an integer
	> Used to calculate late coupons left based on the late days of previous homeworks, and to save output files.

2.  Raw gradescope file from the folder `./Raw_gradescope_grades`
    
3.  Latest Canvas gradebook from the folder `./Gradebook_from_canvas`
    
4.  Enter the weights for each of the 2 problems
    > Each problem is always worth 50% of the whole assignment. However, if a problem has multiple parts, you can assign those parts any set of weights that add up to 1.

5.  If there was any student who received late extensions, select their name → enter the # of days → Add
    > You can type in the “Student name” input field and will get suggestions based on what you type. Hit enter to select a suggestion. Note that there’s also student ID next to each student’s name to help distinguish in the situation that there are 2 students with the exact same name.

6.  After making sure all the steps above are correct, click on “Reformat Grades”.
    > The reformatted gradescope file will be saved to `./Reformatted_grades`. The Canvas gradebook with the current assignment grades and late days will be saved to `./Export_for_canvas`

 
## General notes

- If there are students dropping/getting added to the class, no changes are needed as the grades manager app will automatically assign 0 late days used for new students and disregard the grades of dropped students when exporting converted grades to the Canvas grade book (Tested). 
-   To keep track of late days used history for students, I used a `csv` file located in `Late_days/late_days_history.xlsx`. The first column of this file contains the students’ ID and each subsequent column corresponds to the late days used for each homework.
    > Each late days used cell always have value between 0 and 2 (for example, if a student was 4 days late for homework, since they will have a 0 by the course’s policy, technically no late days were used)

-   If you realize that you input something wrong when reformatting the grades of a homework, simply run the app and convert the grades for that homework again (and all the homwork after that, if there is any).

- By default, HW0's late days are not counted as part of the 6 late days allowance. If you wish to change this, please modify the function `_calculate_final_grades()` in the file `GradesManager.py` at line 164 from "1", to "0"
	```python
	def _calculate_final_grades(self): # with late days policy considered
	        # accumulated late days before this homework
	        accummulated_late_days_dict = defaultdict(lambda: 0) # return 0 by default
	        # before HW1, everyone has 0 late days used, so use defaultdict above
	        if self.HOMEWORK_NO > 1: # <-- CHANGE THIS LINE
	            for i in range(self.late_days_history.shape[0]):
	                student_id = self.late_days_history.iloc[i]['SID']
	```
 

## Dev notes

There are 2 main files:

-   `app.py`: built with tkinter, contains mainly the GUI code with inputs handler, inputs validation, messages, etc.
    
-   `GradesManager.py`: Contains a class that is used for every grades reformatting task such as:
	-   Converting raw grades from a scale of 0 → 6 to 0 → 100
    
	-   Calculating the number of raw late days
    
	-   Calculating the number of late days used in the past
    
	-   Calculate the actual late days used, late coupons used, and penalty
	-   …
    

Every such task usually has its own function, so if you want to modify/learn more about some functionality, look for such function.

-   When populating a Canvas gradebook file, I look for key words such as “Homework ..” or “Late days …“. I’m not sure if these column names will change based on how an instructor setup the course on Canvas (for example, if they use “Assignment 1,2,3,..” instead of “Homework 1,2,3,...”. Therefore, be aware of this if you run into any error and update the codes in file `GradesManager.py` lines 58 to 66 and 140.
    
-   Similarly, when extracting grades from a raw gradescope grades file and finding out how many parts each problem has, I used the following rules:
	- Raw grades start from column 14 (after columns such as (name, student id, lateness, etc.) 
	- Every part of problem 1 has prefix 1 (e.g. 1.1: a, 1.2: b) 

These rules are correct and consistent with every homework. However, in the event that Gradescope decides to change their output file format, watch out for these notes and change the code accordingly (for the file `GradesManager.py`)
