import pandas as pd
import math
from collections import defaultdict
from copy import deepcopy

class GradesManager():

    # if exam=True, calculate grades for exam (without late days) and export to "Exam HOMEWORK_NO" column in Canvas Gradebook instead
    def __init__(self, raw_grades, homework_number: int, late_days_history, extensions=defaultdict(lambda:0), exam=False): # expect pandas dataframes and int
        self.ISEXAM = exam
        self.HOMEWORK_NO = homework_number
        self.raw_grades = raw_grades
        self.late_days_history = late_days_history
        self.final_grades = None # used to store formatted grades

        # Count number of parts for each of the 2 problem P1, P2
        self.P1_num_parts = 0
        self.P2_num_parts = 0
        for col in self.raw_grades.columns[13:]: # Index 13 is always where actual grades start
            if col[0] == '1':
                self.P1_num_parts += 1
            elif col[0] == '2':
                self.P2_num_parts += 1

        # extensions
        self.extensions = extensions

    def reformat_hw_grades(self, P1_weights, P2_weights, save=True):
        self._convert_grades_to_scale_100(P1_weights, P2_weights)
        self._calculate_late_days_since_deadline()
        self.final_grades = self._calculate_final_grades() # with late days policy considered

        # save final grades
        if save == True:
            self.final_grades.to_excel("./Reformatted_grades/HW{}_Final_Grades.xlsx".format(self.HOMEWORK_NO), index=False)

        return self.final_grades # reformatted grades


    def update_historical_late_days_file(self): # must run reformat_hw_grades() before calling this function
        # for merging
        ids_with_late_days_used = self.final_grades[['SID', 'Late Days Used']]

        # Merge on student id, update current HW col, then delete the merged col
        CUR_HW_COL = 'HW' + str(self.HOMEWORK_NO)
        late_days_history = self.late_days_history.merge(ids_with_late_days_used, on='SID', how='right')
        late_days_history[CUR_HW_COL] = late_days_history['Late Days Used']
        late_days_history.drop('Late Days Used', axis=1, inplace=True) # redundant now

        # save updated file
        late_days_history.to_excel("./Late_days/late_days_used_history.xlsx", index=False)


    def export_hw_grades_to_canvas_gradebook(self, canvas_gradebook_path): # must run reformat_hw_grades() before calling this function
        canvas_df = pd.read_csv(canvas_gradebook_path)
        HOMEWORK_COL = None
        LATEDAYS_COL = None
        STUDENT_ID_COL = 'SIS User ID' # according to canvas export in 2022
        HOMEWORK_COL_PREFIX_LEN = 10 # e.g prefix with "Homework 9" --> len=10
        if self.HOMEWORK_NO > 9:
            HOMEWORK_COL_PREFIX_LEN = 11 # e.g "Homework 10" --> len=11

        for col in canvas_df.columns:
            if col[:HOMEWORK_COL_PREFIX_LEN] == 'Homework {}'.format(self.HOMEWORK_NO):
                if 'Late' not in col:
                    HOMEWORK_COL = col
                else:
                    LATEDAYS_COL = col

        # canvas grades
        canvas_grades_df = deepcopy(canvas_df.iloc[2:,]) # skip over the first 2 lines below the header line to get to actual students' data

        # converted gradescope grades
        reformatted_grades = self.final_grades
        reformatted_grades = deepcopy(reformatted_grades[['SID', 'Late Days Used', 'Final Grade']]) # only need student id & final grade
        reformatted_grades.rename({'SID':'SIS User ID', 'Final Grade': 'This Homework Grade'}
                                  , axis=1, inplace=True) # rename to match canvas file for mergin

        # left merging (left outer join) & populate data to canvas grades file
        canvas_grades_df = canvas_grades_df.merge(reformatted_grades, on='SIS User ID', how='left')
        canvas_grades_df[HOMEWORK_COL] = canvas_grades_df['This Homework Grade']
        canvas_grades_df[LATEDAYS_COL] = canvas_grades_df['Late Days Used']
        canvas_grades_df.drop(['Late Days Used', 'This Homework Grade'], axis=1, inplace=True)


        # put updated grades back to original canvas file to match Canvas' expected import format
        canvas_df.loc[2:, HOMEWORK_COL] = canvas_grades_df[HOMEWORK_COL].values
        canvas_df.loc[2:, LATEDAYS_COL] = canvas_grades_df[LATEDAYS_COL].values

        # save
        canvas_df.to_csv("Export_for_canvas/canvas_grades_book.csv", index=False)


    def _convert_grades_to_scale_100(self, P1_weights, P2_weights): # inputs: weights of parts of problem 1 & 2

        def get_calc_avg_grade_func(weights):
            conversion_dict = {
                0: 0,
                1: 10,
                2: 25,
                3: 50,
                4: 75,
                5: 90,
                6: 100
                }
            def calc_avg_grade(row): # each row contains grades of all parts of a problem on scale 6
                weighted_average = 0
                for score,weight in zip(row, weights):
                    if int(score) != float(score):
                        error_mess = "Error: Raw scores must be integers"
                        print(error_mess)
                        return error_mess
                    score = conversion_dict[int(score)] # scale 6 to scale 100
                    weighted_average += score*weight
                return weighted_average

            return calc_avg_grade # return a function to use with pandas.apply()


        # fill missing values for numerical grades with 0
        P1_n_P2_grades = self.raw_grades.iloc[:, 13:(13+ self.P1_num_parts + self.P2_num_parts)]
        P1_n_P2_grades.fillna(0, inplace=True)

        # Calc grades for Problem 1
        P1_grades = P1_n_P2_grades.iloc[:, 0:self.P1_num_parts]
        self.raw_grades['P1'] = P1_grades.apply(get_calc_avg_grade_func(P1_weights), axis=1)

        # Calc grades for Problem 2
        P2_grades = P1_n_P2_grades.iloc[:, self.P1_num_parts:(self.P1_num_parts+self.P2_num_parts)]
        self.raw_grades['P2'] = P2_grades.apply(get_calc_avg_grade_func(P2_weights), axis=1)

        # Calc Average Grades (before considering late days)
        self.raw_grades['Grade'] = (self.raw_grades['P1'] + self.raw_grades['P2'])/2



    def _calculate_late_days_since_deadline(self): # extract late days since deadline for each submission
        # keys: student ids, value: late days since deadline for this homework
        late_days_dict = {}

        # fill missing lateness values
        self.raw_grades['Lateness (H:M:S)'].fillna('00:00:00', inplace=True)

        # convert lateness in "H:M:S" to late days
        def get_num_late_days(row):
            student_id, raw_lateness = row['SID'], row['Lateness (H:M:S)']
            h,m,s = map(lambda x: int(x), raw_lateness.split(':'))
            # Not using seconds to resolve the gradescope discrepancy
            # where if the deadline is 23:59, solution that got submitted
            # at 23:59:XX where XX > 0 will be counted as late, but still
            # showed up on Gradescope as on time --> not using second will
            # basically move the deadline to 00:00 under the hood and resolve this discrepancy.
            cur_late_days = math.ceil((h + m/60) / 24)
            cur_late_days = max(0, cur_late_days - self.extensions[student_id]) # extensions
            late_days_dict[student_id] = cur_late_days
            return cur_late_days

        # convert late time from H:M:S format to days (rounded up)
        #  (0.1 day --> 1 late day, 1.1 days --> 2 late days)
        self.raw_grades['Late Days'] = self.raw_grades.apply(get_num_late_days, axis=1)


    def _calculate_final_grades(self): # with late days policy considered
        # accumulated late days before this homework
        accummulated_late_days_dict = defaultdict(lambda: 0) # return 0 by default
        if self.HOMEWORK_NO > 1: # before HW1, everyone has 0 late days used, so use defaultdict above
            for i in range(self.late_days_history.shape[0]):
                student_id = self.late_days_history.iloc[i]['SID']
                student_past_late_days_used = self.late_days_history.iloc[i,1:self.HOMEWORK_NO+1]
                accummulated_late_days_dict[student_id] = sum(student_past_late_days_used)


        # if lateness >= 3 --> score = 0 --> no late days used
        def get_actual_late_days_used(row): # row is from ids_with_latedays dataframe
            student_id, late_days = row[['SID', 'Late Days']]
            if late_days == 0 or late_days > 3:
                return 0
            past_late_days_used = accummulated_late_days_dict[student_id]
            late_days_left = 6 - past_late_days_used
            late_days_can_use = min(2, late_days_left) # can only use at most 2 coupons for each HW
            actual_late_days_used = late_days if late_days_can_use >= late_days else late_days_can_use
            return actual_late_days_used


        def get_penalty(row): # penalty with late coupons considred
            student_id, grade, uncompensated_late_days = row[['SID', 'Grade', 'Uncompensated Late Days']]
            return min(grade, 25*uncompensated_late_days) # penalty cannot be greater than grade

        self.raw_grades['Late Days Used'] = self.raw_grades.apply(get_actual_late_days_used, axis=1)
        self.raw_grades['Uncompensated Late Days'] = self.raw_grades['Late Days'] - self.raw_grades['Late Days Used']
        self.raw_grades['Penalty'] = self.raw_grades.apply(get_penalty, axis=1)
        self.raw_grades['Final Grade'] = self.raw_grades['Grade'] - self.raw_grades['Penalty']

        return self.raw_grades
