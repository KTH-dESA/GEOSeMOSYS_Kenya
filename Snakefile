rule test:
	input:
		"test_sample.py"
	shell:
		"python -m unittest {input}"

rule download_files:
	input:
		"Download_files.py"
	shell:
		"python {input}"

#rule run_python:
#	input:
#		"Generate_XY_files_ALL_Vision.py",
#		"Kenya_data_input_ALL_Vision_DS_EE"
#		"Kenya_BIG_ALL_Vision2.txt"
#	output:
#		"vision_data.txt"
#	#conda:
#		#"envs/mapping.yaml"
#	shell:
#		"python {input} {output}"




	
