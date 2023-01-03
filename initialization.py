import os
import pandas as pd

required_folders = ['Export_for_canvas', 'Gradebook_from_canvas', 'Late_days', 'Raw_gradescope_grades', 'Reformatted_grades']

for folder in required_folders:
	if not os.path.isdir(folder):
		os.mkdir(folder)

late_days_history_path = 'Late_days/test.xlsx'
if not os.path.isfile(late_days_history_path):
	columns = ['SID'] + ['HW' + str(num) for num in range(1,12)]
	late_days_df = pd.DataFrame(columns=columns)
	late_days_df.to_csv(late_days_history_path, index=False)
